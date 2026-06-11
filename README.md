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

### Docker（推荐，NAS / 服务器一键部署）

在 NAS 上创建 `docker-compose.yml`：

```yaml
services:
  me:
    build:
      context: https://github.com/Metruee/Me.git
      dockerfile: backend/Dockerfile
    container_name: me
    environment:
      - ME_HOME=/app/me_data
      - ME_APP_ROOT=/app
      - ME_STATIC_DIR=/app/static
      - LLM_API_BASE=http://你的模型IP:11434/v1
      - LLM_MODEL=qwen2.5:7b
      - EMBEDDING_API_BASE=http://你的模型IP:11434/v1
      - EMBEDDING_MODEL=nomic-embed-text
    ports:
      - "6868:6868"
    volumes:
      - ./me_data:/app/me_data
      - ./reports:/app/reports
      - ./chroma_data:/app/chroma_data
      - ./uploads:/app/data/uploads
    restart: unless-stopped
```

然后 `docker compose up -d`，访问 `http://NAS_IP:6868`。

Docker 会自动从 GitHub 拉源码、编译前端、安装 Python 依赖。数据全部持久化在本地目录，升级不丢失。

> 如果 GitHub 直连不稳定，可以先 `git clone https://github.com/Metruee/Me.git && cd Me`，然后用 repo 自带的 `docker-compose.yml`（context 为 `.`）本地构建。

### 开发环境

```bash
# 1. 安装依赖
cd 04-APP/backend
pip install -r requirements.txt

cd ../frontend
npm install

# 2. 构建前端
npm run build

# 3. 配置环境变量
# 在 backend 目录下或系统环境变量中设置 LLM_API_BASE 等

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
