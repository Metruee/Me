from __future__ import annotations
"""
ToolRegistry — 工具注册与执行（参考 Zleap-Agent ToolDefinition）

支持：
- 内置工具（web_search, web_fetch）
- 技能扩展工具（SKILL.md 中声明的工具）
- 工具按 expert 绑定
"""
import json
import logging
import urllib.parse
import urllib.request
from typing import Any, Callable, Optional
from core.config import SKILLS_DIR
from core.db import get_db

logger = logging.getLogger("me-backend")

# 工具定义结构
ToolHandler = Callable[..., str]

class ToolDefinition:
    def __init__(self, name: str, description: str, parameters: dict,
                 handler: ToolHandler, enabled_for: Optional[list[str]] = None):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.enabled_for = enabled_for or []  # 空列表表示对所有专家可用

    def to_openai_spec(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def list_for_expert(self, expert_id: str) -> list[ToolDefinition]:
        """返回某专家可用的工具列表"""
        result = []
        for t in self._tools.values():
            if not t.enabled_for or expert_id in t.enabled_for:
                result.append(t)
        return result

    def get_openai_tools(self, expert_id: str) -> list[dict]:
        """返回某专家的 OpenAI 工具定义格式"""
        return [t.to_openai_spec() for t in self.list_for_expert(expert_id)]

    def execute(self, name: str, args: dict) -> str:
        tool = self._tools.get(name)
        if tool:
            return tool.handler(**args)
        # Fallback: 检查技能注册的工具
        for sid in _get_enabled_tools():
            fm = _read_skill_frontmatter(SKILLS_DIR / sid / "SKILL.md")
            for t in (fm.get("tools") or []):
                if isinstance(t, dict) and t.get("name") == name:
                    handler = t.get("handler", "")
                    if handler == "web_search":
                        return _do_web_search(args.get("query", ""), args.get("count", 5))
                    if handler == "web_fetch":
                        return _do_web_fetch(args.get("url", ""), args.get("max_chars", 4000))
        return f"未知工具: {name}"


# ─── 内置工具实现 ───────────────────────────────────

def _do_web_search(query: str, count: int = 5) -> str:
    """搜索互联网"""
    engine = "duckduckgo"
    engines = {
        "google": "https://www.google.com/search?q=",
        "bing": "https://www.bing.com/search?q=",
        "baidu": "https://www.baidu.com/s?wd=",
        "duckduckgo": "https://html.duckduckgo.com/html/?q=",
    }
    url = engines.get(engine, engines["duckduckgo"]) + urllib.parse.quote(query)
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; MeBot/1.0)"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"搜索失败: {e}"
    # 提取链接和标题
    import re
    links = []
    for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', content, re.IGNORECASE):
        href = m.group(1)
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if title and len(title) > 2:
            links.append({"title": title, "url": href})
            if len(links) >= count:
                break
    if not links:
        return f"未找到关于「{query}」的搜索结果。"
    result = [f"📡 搜索「{query}」结果:\n"]
    for i, link in enumerate(links, 1):
        result.append(f"{i}. {link['title']}\n   {link['url']}")
    return "\n".join(result)


def _do_web_fetch(url: str, max_chars: int = 4000) -> str:
    """抓取网页内容"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; MeBot/1.0)"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "application/pdf" in content_type:
                return f"[PDF 文件: {url}] 暂不支持直接读取 PDF 内容，请下载后上传。"
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"读取失败: {e}"
    import re
    # 移除 script 和 style
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # 提取文本
    text = re.sub(r'<[^>]+>', '\n', html)
    text = re.sub(r'\n\s*\n', '\n', text).strip()
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 10]
    result = '\n'.join(lines)
    if len(result) > max_chars:
        result = result[:max_chars] + '\n...(截断)'
    return result or f"未能提取到 {url} 的正文内容。"


# ─── 技能工具扫描 ──────────────────────────────────

def _get_enabled_tools() -> list:
    tools = []
    try:
        if SKILLS_DIR.exists():
            for d in SKILLS_DIR.iterdir():
                if d.is_dir() and (d / "SKILL.md").exists():
                    sid = d.name
                    db2 = get_db()
                    row = db2.execute("SELECT enabled FROM skills WHERE id=?", [sid]).fetchone()
                    db2.close()
                    if not row or row["enabled"]:
                        tools.append(sid)
    except:
        pass
    return tools


def _read_skill_frontmatter(skill_path) -> dict:
    """读取 SKILL.md 的 frontmatter"""
    fm = {}
    try:
        text = skill_path.read_text(encoding="utf-8")
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                import yaml
                fm = yaml.safe_load(parts[1]) or {}
    except:
        pass
    return fm


# ─── 注册所有内置工具 ─────────────────────────────

def register_builtin_tools(registry: ToolRegistry):
    """注册所有内置工具"""
    registry.register(ToolDefinition(
        name="web_search",
        description="搜索互联网获取实时信息。当用户问及热点新闻、实时事件、最新资讯、事实查证时使用。返回搜索结果摘要列表。",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "count": {"type": "integer", "description": "返回条数，默认 5, 最大 10"},
            },
            "required": ["query"],
        },
        handler=lambda query="", count=5: _do_web_search(query, min(int(count), 10)),
        enabled_for=["chiyou", "taishiling"],
    ))
    registry.register(ToolDefinition(
        name="web_fetch",
        description="抓取指定 URL 的网页内容，提取正文文本。用于阅读搜索结果中的具体文章。",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "要抓取的网页 URL"},
                "max_chars": {"type": "integer", "description": "最大返回字符数，默认 4000"},
            },
            "required": ["url"],
        },
        handler=lambda url="", max_chars=4000: _do_web_fetch(url, int(max_chars)),
        enabled_for=["chiyou", "taishiling"],
    ))
    # 从技能加载扩展工具
    for sid in _get_enabled_tools():
        fm = _read_skill_frontmatter(SKILLS_DIR / sid / "SKILL.md")
        for t in (fm.get("tools") or []):
            if isinstance(t, dict) and t.get("name"):
                handler_name = t.get("handler", "")
                if handler_name == "web_search":
                    registry.register(ToolDefinition(
                        name=t["name"],
                        description=t.get("description", ""),
                        parameters=t.get("parameters", {}),
                        handler=lambda q="", c=5: _do_web_search(q, c),
                    ))
                elif handler_name == "web_fetch":
                    registry.register(ToolDefinition(
                        name=t["name"],
                        description=t.get("description", ""),
                        parameters=t.get("parameters", {}),
                        handler=lambda u="", m=4000: _do_web_fetch(u, m),
                    ))


# 全局单例
tool_registry = ToolRegistry()
register_builtin_tools(tool_registry)
