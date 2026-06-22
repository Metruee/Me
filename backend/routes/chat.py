from __future__ import annotations
"""
聊天 API（核心路由）
"""
import json
import logging
import threading
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from core.db import get_db
from core.models import ChatRequest, ChatResponse, EXPERT_DOMAINS
from context.assembly import build_messages, should_include_tools
from providers.registry import llm
from tools.registry import tool_registry
from memory.orchestrator import extract_impression_from_chat, extract_event_from_chat

logger = logging.getLogger("me-backend")
router = APIRouter()


# ─── Helper: 获取有效专家 ID ──────────────────────

def _get_valid_expert_ids() -> list:
    db = get_db()
    try:
        rows = db.execute("SELECT id FROM skills WHERE enabled=1 AND id LIKE 'expert_%'").fetchall()
        db.close()
        builtin = list(EXPERT_DOMAINS.keys())
        return builtin + [r["id"] for r in rows]
    except:
        db.close()
        return list(EXPERT_DOMAINS.keys())


# ─── 自动专家路由 ────────────────────────────────

def _auto_route_expert(message: str, session_id: str) -> Optional[str]:
    """检测用户消息是否需要调用其他专家（自动路由 + 召唤检测）"""
    # 召唤检测
    from core.models import EXPERT_SUMMON
    for eid, sname in EXPERT_SUMMON.items():
        if sname in message and len(message) < 15:
            return eid
    # LLM 分类路由
    db = get_db()
    try:
        api_base, model = None, None
        r1 = db.execute("SELECT value FROM settings WHERE key='llm_api_base'").fetchone()
        r2 = db.execute("SELECT value FROM settings WHERE key='llm_model'").fetchone()
        if r1: api_base = r1["value"]
        if r2: model = r2["value"]
        if not model:
            return None
        valid_ids = _get_valid_expert_ids()
        # 构建分类 prompt
        domain_descs = {eid: f"{eid}({domain})" for eid, domain in EXPERT_DOMAINS.items()
                        if eid in valid_ids}
        # 从技能表加载扩展专家
        try:
            rows = db.execute("SELECT id, label, description FROM skills WHERE enabled=1 AND id LIKE 'expert_%'").fetchall()
            for r in rows:
                domain_descs[r["id"]] = f"{r['id']}({r['label'] or '自定义专家'})"
        except:
            pass
        domain_text = ", ".join(f"{k}: {v}" for k, v in domain_descs.items())
        prompt = (
            f"根据用户消息内容，从以下 expert 中选择最匹配的一个。"
            f"只输出 expert_id，不要解释。\n\n可选: {domain_text}\n\n消息: {message}"
        )
        result = llm.classify(prompt, valid_ids)
        if result and result != "taishiling":
            return result
    except:
        pass
    finally:
        db.close()
    return None


# ─── 智能归档 ────────────────────────────────────

def _detect_archive_intent(message: str) -> bool:
    keywords = ["归档", "收藏", "记录一下", "记下来", "保存", "存档", "存一下", "收录"]
    return any(kw in message for kw in keywords)


def _count_expert_rounds(db, session_id: str, expert_id: str) -> int:
    rows = db.execute(
        "SELECT role FROM conversations WHERE session_id=? AND expert_id=? ORDER BY id DESC LIMIT 40",
        [session_id, expert_id]
    ).fetchall()
    count = 0
    for r in rows:
        if r["role"] == "user":
            count += 1
        else:
            break
    return count


def _dedup_check(db, text: str) -> bool:
    recent = db.execute(
        "SELECT summary, original_text FROM knowledge_entries ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    if not recent:
        return False
    words = set(text[:200].split())
    for r in recent:
        existing = (r["summary"] or "") + (r["original_text"] or "")[:500]
        existing_words = set(existing.split())
        if existing_words and words:
            overlap = len(words & existing_words) / max(len(words | existing_words), 1)
            if overlap > 0.6:
                return True
    return False


def _classify_theme(text: str) -> str:
    from core.models import EXPERT_DOMAINS
    domain_keywords = {
        "自我核心": ["情绪", "焦虑", "恐惧", "性格", "自卑", "自信", "成长", "自我"],
        "事业": ["工作", "事业", "创业", "职场", "老板", "同事", "项目", "升职", "跳槽"],
        "财富": ["钱", "财务", "投资", "理财", "收入", "消费", "买房", "负债", "省钱"],
        "人性": ["欲望", "贪婪", "诱惑", "习惯", "上瘾", "冲动", "克制"],
        "亲密关系": ["关系", "伴侣", "恋爱", "婚姻", "家庭", "父母", "朋友", "吵架", "沟通"],
        "健康": ["健康", "身体", "睡眠", "运动", "饮食", "压力", "疲惫", "病"],
    }
    for domain, kws in domain_keywords.items():
        if any(kw in text for kw in kws):
            return domain
    return "未归类"


def _llm_archive_summarize(db, session_id: str, expert_id: str) -> dict:
    if not llm.is_configured():
        return {}
    recent = db.execute(
        "SELECT role, content FROM conversations WHERE session_id=? AND expert_id=? ORDER BY id DESC LIMIT 20",
        [session_id, expert_id]
    ).fetchall()
    if not recent:
        return {}
    recent = list(reversed(recent))
    lines = [f"{'用户' if m['role'] == 'user' else '专家'}: {m['content'][:300]}"
             for m in recent]
    conversation_text = "\n".join(lines)
    full_text = "\n".join([f"{'用户' if m['role'] == 'user' else '专家'}: {m['content']}"
                          for m in recent])
    prompt = (
        "你是一位知识提炼专家。请从以下对话中提取核心主题和关键信息。\n\n"
        "对话内容：\n" + conversation_text + "\n\n"
        "请用JSON输出，包含两个字段：\n"
        '  - theme: 主题归类（自我核心/事业/财富/人性/亲密关系/健康/其他）\n'
        '  - summary: 核心摘要（<200字）\n'
        "只输出JSON，不要其他文字。"
    )
    try:
        result = llm.chat(messages=[{"role": "user", "content": prompt}],
                          temperature=0.3, max_tokens=500)
        text = result.get("content", "").strip()
        if text:
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            parsed = json.loads(text)
            parsed["full_text"] = full_text
            return parsed
    except:
        pass
    return {}


def _kb_archive(entry_id: str, theme: str, summary: str, text: str):
    """后台归档到 ChromaDB"""
    try:
        from providers.registry import embedding
        emb = embedding.embed(summary[:500])
        if not emb:
            return
        import chromadb
        from core.config import CHROMA_PATH
        client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=chromadb.config.Settings(anonymized_telemetry=False),
        )
        coll = client.get_or_create_collection(
            name="me_knowledge", metadata={"hnsw:space": "cosine"},
        )
        coll.add(
            ids=[entry_id],
            embeddings=[emb],
            metadatas=[{"theme_main": theme, "expert_id": ""}],
            documents=[summary[:500]],
        )
    except Exception as e:
        logger.warning(f"ChromaDB archive failed: {e}")


# ─── KB search ────────────────────────────────────

def _kb_search(query: str, domain: str = "", limit: int = 5) -> str:
    from providers.registry import embedding
    entries = []
    try:
        import chromadb
        from core.config import CHROMA_PATH
        client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=chromadb.config.Settings(anonymized_telemetry=False),
        )
        coll = client.get_or_create_collection(
            name="me_knowledge", metadata={"hnsw:space": "cosine"},
        )
        emb = embedding.embed(query)
        if emb:
            where = None if (not domain or domain == "all") else {"theme_main": domain}
            r = coll.query(query_embeddings=[emb], n_results=limit, where=where,
                          include=["metadatas", "documents", "distances"])
            if r and r.get("documents") and r["documents"][0]:
                for i, doc in enumerate(r["documents"][0]):
                    meta = r["metadatas"][0][i]
                    entries.append(f"[{meta.get('theme_main', '')}] {doc[:200]}")
    except Exception as e:
        logger.warning(f"ChromaDB search failed: {e}")
    if not entries:
        db = get_db()
        try:
            words = [w for w in query.split() if len(w) > 1][:5]
            if words:
                sql = "SELECT * FROM knowledge_entries WHERE " + " OR ".join(
                    "(summary LIKE ? OR original_text LIKE ?)" for _ in words
                ) + " ORDER BY created_at DESC LIMIT ?"
                params = []
                for w in words:
                    params.extend([f"%{w}%", f"%{w}%"])
                params.append(limit)
                for r in db.execute(sql, params).fetchall():
                    entries.append(f"[{r['theme_main']}] {r['summary'][:200]}")
        except:
            pass
        finally:
            db.close()
    return "\n".join(entries) if entries else ""


# ─── 工具对话 ────────────────────────────────────

def _chat_with_tools(llm_base: str, model: str, messages: list,
                     expert_id: str) -> str:
    """支持工具调用的 LLM 对话"""
    from core.config import LLM_BASE
    tools = None
    if should_include_tools(expert_id):
        tools = tool_registry.get_openai_tools(expert_id)
    reply_parts = []
    max_rounds = 5
    for _ in range(max_rounds):
        try:
            result = llm.chat(messages=messages, tools=tools)
        except Exception as e:
            logger.warning(f"LLM chat failed: {e}")
            if reply_parts:
                break
            raise
        content = result.get("content", "")
        if content:
            reply_parts.append(content)
        tool_calls = result.get("tool_calls")
        if not tool_calls:
            break
        messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
        for tc in tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")
            try:
                args = json.loads(func.get("arguments", "{}"))
            except:
                args = {}
            logger.info(f"Executing tool: {name} args={args}")
            tool_result = tool_registry.execute(name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": tool_result,
            })
        # 第二圈之后不再带 tools，减少 token 消耗
        if _ >= 2:
            tools = None
    return "\n".join(p for p in reply_parts if p)


# ─── 主聊天入口 ─────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    db = get_db()
    current_expert_id = req.expert_id or "taishiling"
    auto_expert_id = None
    auto_system_message = ""
    reply = ""
    llm_error = ""

    # ══ 1. 自动路由检测 ═══
    routed = _auto_route_expert(req.message, req.session_id)
    if routed and routed != current_expert_id:
        auto_expert_id = routed
        auto_system_message = f"🔮 此事更适合{EXPERT_DOMAINS.get(routed, '')}领域，已召{'taishiling' if routed == 'taishiling' else routed}前来。"
        if routed == "cangjie":
            auto_system_message = "✍️ 已召仓颉前来为你记录道痕。请如实道来——发生了什么？"

    # ══ 2. 加载历史（自动路由到新专家时只带系统消息）═══
    if auto_expert_id:
        history = []
    else:
        history_rows = db.execute(
            "SELECT role, content FROM conversations WHERE session_id=? AND expert_id=? ORDER BY id ASC",
            [req.session_id, current_expert_id]
        ).fetchall()
        history = [{"role": r["role"], "content": r["content"]} for r in history_rows]
    # 边界保护：最长 40 条
    if len(history) > 40:
        history = history[-40:]

    # ══ 3. 构建 prompt（Context Assembly）═══
    messages = build_messages(
        expert_id=auto_expert_id or current_expert_id,
        history=history,
        user_message=req.message,
        include_memory=(not auto_expert_id),  # 切换专家时不带入记忆
    )

    # ══ 4. KB 增强检索（只在有历史时做）═══
    if not auto_expert_id and len(history) > 2:
        try:
            kb_text = _kb_search(req.message, domain=EXPERT_DOMAINS.get(current_expert_id, ""))
            if kb_text:
                messages.insert(0, {
                    "role": "system",
                    "content": f"## 知识库相关条目\n{kb_text}",
                })
        except:
            pass

    messages.append({"role": "user", "content": req.message})

    # ══ 5. 调用 LLM ═══
    try:
        if not llm.is_configured():
            raise Exception("LLM 模型未配置")
        llm_reply = _chat_with_tools(
            llm.api_base, llm.model, messages,
            auto_expert_id or current_expert_id,
        )
        if llm_reply:
            reply = llm_reply
        else:
            llm_error = "LLM 返回为空"
    except Exception as e:
        logger.warning(f"LLM chat failed: {e}")
        llm_error = "模型响应超时或不可用，已自动重试，请稍后再试"

    # ══ 6. 存对话记录 ═══
    db.execute("INSERT INTO conversations(session_id,role,content,expert_id) VALUES(?,?,?,?)",
               [req.session_id, "user", req.message, current_expert_id])
    if reply and not llm_error:
        db.execute("INSERT INTO conversations(session_id,role,content,expert_id) VALUES(?,?,?,?)",
                   [req.session_id, "assistant", reply, current_expert_id])

    # ══ 7. 自动提取记忆（后台异步）═══
    if reply and not llm_error:
        extract_impression_from_chat(req.session_id, current_expert_id, req.message, reply)
        extract_event_from_chat(req.session_id, current_expert_id, req.message, reply)

    # ══ 8. 智能归档判断 ═══
    archived = False
    archive_system_msg = ""
    auto_archive = True
    try:
        aa = db.execute("SELECT value FROM settings WHERE key='auto_archive'").fetchone()
        if aa:
            auto_archive = aa["value"].lower() in ("true", "1", "yes", "on")
    except:
        pass

    should_archive = False
    archive_reason = ""

    if auto_archive and _detect_archive_intent(req.message):
        should_archive = True
        archive_reason = "user_intent"
    if auto_archive and not should_archive:
        rounds = _count_expert_rounds(db, req.session_id, current_expert_id)
        if rounds >= 20:
            should_archive = True
            archive_reason = "rounds_threshold"
            archive_system_msg = f"📌 当前话题已讨论 {rounds} 轮，为你提炼归档..."
    if req.is_file_upload:
        should_archive = True
        archive_reason = "file_upload"

    if should_archive:
        archive_result = _llm_archive_summarize(db, req.session_id, current_expert_id)
        if archive_result:
            theme = archive_result.get("theme", "未归类")
            summary = archive_result.get("summary", req.message[:200])
        else:
            theme = _classify_theme(req.message)
            summary = req.message[:200]
        if not _dedup_check(db, summary):
            entry_id = f"me_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
            full_text = archive_result.get("full_text", req.message) if archive_result else req.message
            db.execute(
                "INSERT INTO knowledge_entries(id,theme_main,summary,original_text,expert_id) VALUES(?,?,?,?,?)",
                [entry_id, theme, summary, full_text, current_expert_id]
            )
            db.commit()
            threading.Thread(target=_kb_archive, args=(entry_id, theme, summary, full_text)).start()
            archived = True
            archive_system_msg = archive_reason == "user_intent" and f"✅ 已归档到「{theme}」" or \
                archive_reason == "file_upload" and f"📥 文件内容已归档到「{theme}」" or archive_system_msg

    db.commit()
    db.close()
    switch_type = "auto" if auto_expert_id else "none"
    return ChatResponse(
        reply=reply, expert_id=auto_expert_id or current_expert_id,
        switch_type=switch_type,
        system_message=archive_system_msg or auto_system_message,
        archived=archived, llm_error=llm_error,
    )
