"""
Provider Registry — 模型提供者注册与配置管理
"""
import json
import logging
import urllib.request
import urllib.error
from typing import Optional
from core.config import LLM_BASE, LLM_MODEL
from core.db import get_db

logger = logging.getLogger("me-backend")

class LLMConfig:
    """LLM 配置，从 settings 表动态读取"""
    def __init__(self):
        self.api_base: str = LLM_BASE
        self.model: str = LLM_MODEL

    def reload(self):
        try:
            import sqlite3
            from .config import DB_PATH
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            r1 = conn.execute("SELECT value FROM settings WHERE key='llm_api_base'").fetchone()
            r2 = conn.execute("SELECT value FROM settings WHERE key='llm_model'").fetchone()
            if r1 and r1["value"]:
                self.api_base = r1["value"]
            if r2 and r2["value"]:
                self.model = r2["value"]
            conn.close()
        except:
            pass

    def chat(self, messages: list, tools: Optional[list] = None,
             temperature: float = 0.7, max_tokens: int = 2048,
             timeout: int = 180) -> dict:
        """调用 LLM Chat API，自动重试 1 次"""
        self.reload()
        if not self.model:
            raise RuntimeError("LLM 模型未配置")
        base = self.api_base.rstrip("/")
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{base}/chat/completions", data=body,
            headers={"Content-Type": "application/json"},
        )
        last_error = None
        for attempt in range(2):
            try:
                t = timeout if attempt == 0 else min(timeout + 120, 300)
                with urllib.request.urlopen(req, timeout=t) as resp:
                    data = json.loads(resp.read())
                    msg = data["choices"][0]["message"]
                    result = {
                        "content": msg.get("content", ""),
                        "tool_calls": msg.get("tool_calls"),
                    }
                    logger.info(
                        f"LLM model={self.model} "
                        f"content_len={len(result['content'] or '')} "
                        f"tool_calls={len(result['tool_calls'] or [])}"
                    )
                    return result
            except urllib.error.HTTPError as e:
                last_error = e
                if e.code == 400 and len(messages) > 5:
                    slim = [m for m in messages if m["role"] == "system"]
                    for m in reversed(messages):
                        if m["role"] == "user":
                            slim.append(m)
                            break
                    p2 = {**payload, "messages": slim}
                    try:
                        with urllib.request.urlopen(
                            urllib.request.Request(
                                f"{base}/chat/completions",
                                data=json.dumps(p2).encode(),
                                headers={"Content-Type": "application/json"},
                            ),
                            timeout=300,
                        ) as r2:
                            d2 = json.loads(r2.read())
                            m2 = d2["choices"][0]["message"]
                            return {"content": m2.get("content", ""), "tool_calls": m2.get("tool_calls")}
                    except:
                        pass
                break
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_error = e
                if attempt == 0:
                    logger.warning(f"LLM timeout (attempt 1/2), retrying...")
                    continue
                break
            except Exception as e:
                last_error = e
                break
        raise last_error or RuntimeError("LLM call failed after retries")

    def classify(self, prompt: str, valid_ids: list[str]) -> Optional[str]:
        """意图分类：返回匹配的 expert_id"""
        self.reload()
        if not self.model:
            return None
        base = self.api_base.rstrip("/")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个意图分类器。只输出一个单词的 expert_id，不要解释。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 20,
        }
        try:
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/chat/completions", data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                result = data["choices"][0]["message"]["content"].strip().lower()
                for eid in valid_ids:
                    if eid in result:
                        return eid
                return None
        except:
            return None

    def is_configured(self) -> bool:
        self.reload()
        return bool(self.model)


class EmbeddingConfig:
    """Embedding API 配置"""
    def __init__(self):
        self.api_base: str = LLM_BASE
        self.model: str = ""

    def reload(self):
        try:
            import sqlite3
            from .config import DB_PATH
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            r1 = conn.execute("SELECT value FROM settings WHERE key='embedding_api_base'").fetchone()
            r2 = conn.execute("SELECT value FROM settings WHERE key='embedding_model'").fetchone()
            if r1 and r1["value"]:
                self.api_base = r1["value"]
            if r2 and r2["value"]:
                self.model = r2["value"]
            conn.close()
        except:
            pass

    def embed(self, text: str) -> Optional[list]:
        """生成文本向量"""
        self.reload()
        if not self.model:
            return None
        base = self.api_base.rstrip("/")
        payload = json.dumps({"input": text, "model": self.model}).encode()
        req = urllib.request.Request(
            f"{base}/embeddings", data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())["data"][0]["embedding"]
        except Exception as e:
            logger.warning(f"Embedding failed: {e}")
            return None

    def is_configured(self) -> bool:
        self.reload()
        return bool(self.model)


# 全局单例
llm = LLMConfig()
embedding = EmbeddingConfig()
