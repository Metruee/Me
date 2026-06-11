# 自知 · Me

> 八位神话专家，一方烛火。不迎合，不审判，只是照见。

**自知** 是一个本地化的个人智能分析平台。它通过对话记录、道痕日记、知识归档和定期复盘，帮助人观察自己的思想河流——识别反复出现的模式，看清贪梦与恐惧的根源。

## 功能

- **💬 专家对话** — 八位神话人格专家（太史令、钟馗、蚩尤、仓颉、比干、造君、七魄、贪狼），各有专精领域
- **🪨 道痕日记** — 记录情绪事件，"捞石头"，追踪心石模式与贪惧天平
- **📚 档案馆** — 对话提炼为结构化知识条目，语义检索
- **📋 复盘报告** — 定期综合评估，结合知识库 + 道痕 + 历史报告生成画像
- **🔧 技能系统** — 可安装的专家人格和工具插件，支持 .zip 上传

## 隐私优先

**强烈推荐使用本地部署的 LLM**（如 Ollama），所有对话数据、道痕记录、知识库均保存在本地，不上传任何第三方服务。你的思想数据只属于你自己。

## 技术栈

Vue 3 + FastAPI + SQLite + ChromaDB + Docker

## 安装

```bash
# 1. 安装依赖
cd 04-APP/backend
pip install -r requirements.txt

cd ../frontend
npm install

# 2. 构建前端
npm run build

# 3. 配置环境变量（.env 或直接 export）
export ME_HOME=/path/to/data        # 数据目录
export LLM_API_BASE=http://localhost:11434/v1  # Ollama 或其他本地 LLM
export LLM_MODEL=qwen2.5:7b
export EMBEDDING_API_BASE=http://localhost:11434/v1
export EMBEDDING_MODEL=nomic-embed-text

# 4. 启动
cd ../backend
python main.py
# 访问 http://localhost:6868
```

## 说明

本人非专业开发人员，此项目为个人兴趣作品。源码仅供参考，当前成熟度不高，可能存在较多不合理设计或未完善的边界处理。

感兴趣的朋友欢迎共同完善——无论是代码、设计建议还是产品思路，都很欢迎。

## 致谢

感谢 **路飞大神** 的作品 **《人选天选论》** ，促使我开始自我反思，并最终促成了这个项目的诞生。

---

*自知者明，自胜者强。*
