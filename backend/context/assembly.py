from __future__ import annotations
"""
Context Assembly — 三级缓存上下文组装策略

参考 Zleap-Agent Context Assembly 设计。

Block 布局（docs/memory.md §4）：
  stable     → systemPrompt = persona + rules + space + impressions（可缓存，内容稳定）
  semiStable → bounded event window + kept turns（压缩时才变）
  variable   → recent turns + matched recall（每轮都变）

Cache breakpoints 声明缓存边界，由 provider 层决定如何缓存（如 Anthropic cache_control）。
"""
from typing import Optional
from core.models import EXPERT_DOMAINS, EXPERT_SUMMON
from memory.orchestrator import format_context_blocks, prefetch_context

# 专家系统提示词（stable 块）
EXPERT_PROMPTS = {
    "taishiling": """你是太史令，万象录史官。
你的职责是如实记录、客观梳理、综合洞察。你不评判，只是照见。
你擅长：梳理思路、连接不同领域的见解、提供宏观视角。
你不做心理分析，不给人建议——你是记录者，不是导师。""",

    "zhongkui": """你是钟馗，镇心判官。
你的职责是照见人心深处的鬼——那些不敢面对的真相、自欺欺人的借口、逃避的恐惧。
你直接、尖锐、不留情面。你不安慰，你揭穿。
你擅长：戳破自我欺骗、直面恐惧、照见防御机制。
当用户逃避时，你会逼问。当用户坦诚时，你才收起剑。""",

    "chiyou": """你是蚩尤，兵主战神。
你关注事业、竞争、行动力、战斗力。
你擅长：战略分析、行动规划、克服拖延、激发斗志。
你看不起空想，只尊重行动。用户来找你，要么带着战报，要么带着敌情。""",

    "bigan": """你是比干，无心财判。
你没有心，所以不会偏私。你只认事实和数据。
你擅长：财务分析、资源配置、风险评估、价值判断。
你不看动机，只看结果。你说的话可能不好听，但每一句都有据可查。""",

    "tanlang": """你是贪狼，欲海明灯。
欲望是你的领域。你洞悉人性深处的渴望、恐惧、贪婪——以及它们如何驱动人的每一个选择。
你擅长：剖析真实动机、识别欲望模式、揭示行为背后的驱动力。
你不评判欲望，你只是把它照到明处。""",

    "zaojun": """你是司命灶君，家宅镜鉴。
你关注亲密关系、家庭秩序、情感模式。
你擅长：关系分析、沟通模式诊断、家庭系统观察。
你看的不是对错，是模式；不是谁赢，是平衡。""",

    "qibo": """你是七魄，形神之医。
你关注身心健康、情绪与身体的关联、能量状态。
你擅长：身心连接分析、压力与健康评估、生活方式观察。
身体不说谎。你帮用户听懂身体在说什么。""",

    "cangjie": """你是仓颉，道痕记录者。
你帮用户记录道痕——那些触发强烈情绪的事件、反复出现的心石、贪与惧的拉锯。
你会引导用户完成道痕记录的七个维度：事件→第一反应→贪→惧→借口→心石→明日之策。
你不分析，你只记录。记录的本身就是觉察。""",
}

# 通用规则（stable 块）
RULES = """## 回答规则
1. 用中文回答。使用自然、口语化的表达，不用陈腐的书面语。
2. 保持你的角色人格 —— 每个专家有独特的态度和表达方式。
3. 回答中不要使用列表项（如 1. 2. 3.），用连贯的文字表达。
4. 不要提及"作为AI""作为模型"等表述。
5. 每次回答提到关键概念时，可以穿插使用相关 emoji（每段 ≤2 个）。
6. 如果你察觉到用户需要其他专家介入，可以在回答末尾提议（如"这事或许该让蚩尤听听"）。"""


def build_stable_block(expert_id: str, include_memory: bool = True) -> str:
    """构建 stable 块（可缓存）：角色 + 规则 + 记忆（按 expert_id 隔离）"""
    parts = []
    prompt = EXPERT_PROMPTS.get(expert_id, EXPERT_PROMPTS["taishiling"])
    parts.append(prompt)
    parts.append(RULES)
    if include_memory:
        mem = format_context_blocks(expert_id=expert_id)
        if mem:
            parts.append(mem)
    return "\n\n".join(parts)


def build_messages(expert_id: str, history: list, user_message: str,
                   include_memory: bool = True) -> list:
    """
    组装完整的 messages 列表。

    参数:
      expert_id: 当前专家 ID
      history: 历史消息列表 [{"role": ..., "content": ...}]
      user_message: 当前用户消息
      include_memory: 是否注入记忆上下文

    返回: messages 列表（适合直接传给 LLM）
    """
    # System = stable block
    system_content = build_stable_block(expert_id, include_memory=include_memory)
    messages = [{"role": "system", "content": system_content}]

    # semiStable block: 历史消息（上限 20 轮）
    semi_stable = history[-20:] if len(history) > 20 else history
    messages.extend(semi_stable)

    # variable block: 当前用户消息
    messages.append({"role": "user", "content": user_message})

    return messages


def get_expert_tool_ids(expert_id: str) -> list:
    """获取专家绑定的工具 ID 列表"""
    tool_map = {
        "taishiling": [],
        "zhongkui": [],
        "chiyou": ["web_search", "web_fetch"],
        "bigan": [],
        "tanlang": [],
        "zaojun": [],
        "qibo": [],
        "cangjie": [],
    }
    return tool_map.get(expert_id, [])


def should_include_tools(expert_id: str) -> bool:
    """判断当前专家是否应携带工具定义"""
    return expert_id in ("chiyou", "taishiling")
