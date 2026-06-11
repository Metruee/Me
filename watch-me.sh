#!/bin/bash
# 监控 Me 后端 LLM 调用日志
# 用法: bash watch-me.sh
LOG_FILE="/tmp/me-backend.log"

echo "📡 监控 Me 后端对话日志 (Ctrl+C 退出)"
echo "═══════════════════════════════════════"
echo ""

tail -f "$LOG_FILE" | while read line; do
  # 高亮关键事件
  if echo "$line" | grep -q "POST /api/chat"; then
    MSG=$(echo "$line" | grep -o '"message":"[^"]*"' | sed 's/"message":"//;s/"//')
    EXPERT=$(echo "$line" | grep -o '"expert_id":"[^"]*"' | sed 's/"expert_id":"//;s/"//')
    SESSION=$(echo "$line" | grep -o '"session_id":"[^"]*"' | sed 's/"session_id":"//;s/"//')
    if [ -n "$MSG" ]; then
      echo ""
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo "💬 用户消息 → $EXPERT | 会话: $SESSION"
      echo "   内容: $MSG"
    fi
  elif echo "$line" | grep -q "LLM call model="; then
    MODEL=$(echo "$line" | grep -o "model=[^ ]*" | sed 's/model=//')
    LEN=$(echo "$line" | grep -o "content_len=[0-9]*" | sed 's/content_len=//')
    TOOLS=$(echo "$line" | grep -o "tool_calls=[0-9]*" | sed 's/tool_calls=//')
    echo "   🧠 模型: $MODEL | 回复长度: ${LEN}字 | 工具调用: ${TOOLS}次"
  elif echo "$line" | grep -q "LLM retry OK"; then
    LEN=$(echo "$line" | grep -o "content_len=[0-9]*" | sed 's/content_len=//')
    echo "   🔄 重试成功 | 回复长度: ${LEN}字"
  elif echo "$line" | grep -q "tool round="; then
    ROUND=$(echo "$line" | grep -o "tool round=[0-9]*" | sed 's/tool round=//')
    echo "   🔧 工具轮次: $ROUND"
  elif echo "$line" | grep -q "tool name="; then
    NAME=$(echo "$line" | grep -o "name=[^ ]*" | sed 's/name=//')
    RES_LEN=$(echo "$line" | grep -o "result_len=[0-9]*" | sed 's/result_len=//')
    echo "   📎 工具: $NAME | 结果长度: ${RES_LEN}字"
  elif echo "$line" | grep -q "tool final"; then
    LEN=$(echo "$line" | grep -o "content_len=[0-9]*" | sed 's/content_len=//')
    echo "   ✅ 最终回复长度: ${LEN}字"
  elif echo "$line" | grep -q "LLM 400"; then
    echo "   ⚠️  400 错误，自动重试中…"
  elif echo "$line" | grep -q "LLM chat failed"; then
    echo "   ❌ LLM 调用失败！"
  elif echo "$line" | grep -q "LLM returned empty"; then
    echo "   ⚠️  模型返回空回复！"
  elif echo "$line" | grep -q "Handoff LLM failed"; then
    echo "   ⚠️  路由交接 LLM 失败！"
  elif echo "$line" | grep -q "WARNING\|ERROR"; then
    echo "   ⚡ $(echo "$line" | grep -o 'WARNING.*\|ERROR.*')"
  fi
done
