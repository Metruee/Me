# 自知 · Me — 产品需求文档（PRD）

> 版本：0.3.0 | 更新：2026-06-12 | 作者：metrue

---

## 目录

1. [产品概述](#1-产品概述)
2. [核心概念](#2-核心概念)
3. [角色体系](#3-角色体系)
4. [功能模块](#4-功能模块)
5. [系统架构](#5-系统架构)
6. [数据模型](#6-数据模型)
7. [API 接口](#7-api-接口)
8. [部署方案](#8-部署方案)
9. [路线图](#9-路线图)

---

## 1. 产品概述

### 1.1 定位

**自知** 是一个本地化的个人智能分析平台。它不替你解决问题、不给鸡汤、不做认知行为疗法——它只做一件事：**帮你看见自己思想的模式**。

### 1.2 核心理念

借用《人选天选论》中"河与石头"的隐喻：

- 人的思想是一条河流：水源 = 外界信息，河床 = 天生经历，石头 = 贪梦与恐惧，波纹 = 借口与自洽
- "道痕"即用回头看的方式辨认走过的路——知道哪些石头反复绊倒了你，你的贪梦核心是什么，恐惧根基在哪里
- 自知不是一步到达的顿悟，而是反复"捞石头"的习惯

### 1.3 隐私原则

- 所有数据（对话、道痕、知识库、向量索引、报告）100% 本地存储
- 推荐使用本地 LLM（Ollama），数据不出机
- 零外部依赖、零埋点、零遥测

### 1.4 目标用户

- 对自我认知有真实需求的人
- 有本地部署能力（NAS / 个人服务器）
- 接受"不迎合、不审判、不替你做决定"的分析风格

---

## 2. 核心概念

### 2.1 六层捞石头

在道痕日记中记录一次情绪事件，按六层深挖：

| 层 | 含义 | 示例 |
|---|---|---|
| 1. 事实 | 发生了什么 | "同事在会议上否定我的方案" |
| 2. 第一反应 | 当时的感觉/行为 | "我立刻反驳，声音都抬高了" |
| 3. 贪梦 | 背后想要的是什么 | "想被认可为有洞察力的人" |
| 4. 恐惧 | 背后怕的是什么 | "怕被当作平庸" |
| 5. 自洽 | 给自己找的理由 | "他们不理解而已" |
| 6. 主石头 | 核心心石（贪/惧的根） | "怕被看轻" |

### 2.2 天权之桥

贪梦和恐惧如同天平两端。大多数痛苦不是因为贪梦或恐惧本身，而是因为**桥倾斜了**——一端压倒另一端。自知不帮你"修复"天平，而是帮你看见它正在倾斜。

### 2.3 道痕

"道"即路径也是言说，"痕"从病字旁加一个艮（回头看的眼睛）。道痕即**用回头看的方式，辨认自己走过的路上留下的痕迹**。

### 2.4 档案化

对话不是流水账。每次对话后，系统自动/手动将对话提炼为一条知识条目——主题、摘要、关键洞察。这样档案馆里存的是精炼的知识，不是聊天记录。

---

## 3. 角色体系

### 3.1 八位神话专家

每位专家有独立的人格提示词（存于 `me_data/skills/me_experts/`），以 Markdown 文件形式可编辑。

| ID | 名称 | 领域 | 人格关键词 | 召唤语 |
|---|---|---|---|---|
| taishiling | 太史令 📜 | 全部（默认） | 史官、记录、调度 | "太史令" |
| zhongkui | 钟馗 ⚔️ | 自我核心 | 锋利、不迎合、直面 | "钟馗" |
| chiyou | 蚩尤 🐉 | 事业 | 果决、战场视角 | "蚩尤" |
| bigan | 比干 ⚖️ | 财富 | 公正、无心无偏 | "比干" |
| tanlang | 贪狼 🐺 | 人性 | 直指欲望 | "贪狼" |
| zaojun | 司命灶君 🔥 | 亲密关系 | 明察、听细节 | "灶君" |
| qibo | 岐伯 🌿 | 健康 | 古朴、身心合一 | "岐伯" |
| cangjie | 仓颉 🏺 | 自知（道痕） | 温和、以字说理 | "仓颉" |

### 3.2 专家协作机制

- **召唤**：用户在对话中说出召唤语（如"钟馗"），太史令自动将上下文交接给目标专家
- **自动路由**：LLM 分析用户消息，匹配最适合的专家领域，太史令生成交接备忘录后切换
- **道痕注入**：仓颉等特定专家对话时自动注入最近 30 条道痕 + 高频心石 Top 5
- **知识库注入**：每次对话注入 ChromaDB 语义搜索匹配的历史知识条目

### 3.3 技能系统（插件化）

- 技能以文件夹形式存放在 `me_data/skills/`
- 每个技能需包含 `SKILL.md`（YAML front matter + Markdown 正文）
- 技能 front matter 支持声明 `tools`，自动注册为 LLM 可调用的 function
- 支持上传 `.zip` 包一键安装技能
- 技能可启用/停用/删除

---

## 4. 功能模块

### 4.1 对话（Chat）

**入口**：首页

- 多会话管理（创建/切换/重命名/删除）
- 对话历史持久化（按 session + expert 存储）
- 用户消息自动检测召唤语
- LLM 回复支持 Markdown 渲染
- 对话支持 function calling（工具调用），最多 3 轮工具循环
- 内置工具：`web_search`（搜索）、`web_fetch`（抓取网页）

**工具执行流程**：
```
用户消息 → LLM 返回 function_call → 执行工具 → 注入结果 → LLM 二次回复
```

### 4.2 道痕日记（Daoben）

**入口**：菜单「道痕」

- **记道痕**：六层捞石头表单（事实 → 第一反应 → 贪梦 → 恐惧 → 自洽 → 主石头）
- **道痕列表**：按时间倒序展示，支持搜索
- **回看仪表盘**：
  - 摘要卡片（道痕总数、不同心石数、分布趋势、贪惧天平）
  - 重复心石 Top 10 条形图
  - 贪/惧天平比例可视化
  - 常用自洽理由排行
  - 每日道痕频率时间线
  - 按周/月/全部筛选
- **心石统计**：重复出现的心石排行

### 4.3 档案馆（Archive）

**入口**：菜单「档案馆」

- **知识条目列表**：按主题（theme_main）分类，支持筛选
- **条目详情**：原始文本、摘要、关联专家、创建时间
- **条目编辑**：修改主题、摘要
- **清除知识库**：清空所有条目
- **文件上传**：上传文件后自动解析为知识条目（支持 txt/pdf 等文本文件）
- 知识条目写入时自动生成 Embedding → 存入 ChromaDB

### 4.4 复盘报告（Report）

**入口**：菜单「复盘」

- **报告生成**：一键生成综合评估报告
- **报告列表**：按生成时间排列，显示精确到分钟的时间
- **报告查看**：浏览器新窗口打开 HTML 报告
- **报告删除**：确认后永久删除（含文件 + 数据库记录）

**报告结构**：
```
## 画像：一段段落式综合描述 + 定性趋势（相较上次，状态由XX变成XX）

## {领域1}
  趋势：与上期对比
  总结：核心发现
  自由洞察

## {领域2}
  ...

## 跨域洞察（可选）

## 风险提示（可选）
```

**报告数据源**：
- 知识库条目（按 theme 分组）
- 道痕数据（心石频次、贪惧统计、常用借口）
- 上期报告摘要（用于趋势对比）

**LLM 约束**：使用 `markdown` 库转换，system prompt 定义了 6 条分析原则（基于证据、客观评价、关注模式、有变化才说、道痕知识库交叉验证、温度冷静）。

### 4.5 专家管理（Expert）

**入口**：菜单「专家」

- **专家列表**：显示所有 8 位专家，含名称、头像、领域、对话风格、召唤语
- **专家配置**：编辑召唤语、回应语、领域描述
- **人格提示词**：每位专家对应一个 Markdown 文件，可在前端编辑
- **重置**：一键恢复默认人格
- **启用/停用**：控制专家是否参与对话和自动路由

### 4.6 技能管理（Skills）

**入口**：菜单「技能」

- **技能列表**：显示技能名称、描述（从 SKILL.md front matter 提取）
- **启用/停用**：控制技能是否注册为 LLM 可用工具
- **上传技能包**：点击或拖拽 `.zip` 文件上传
- **删除技能**：确认后永久删除（含本地文件）

### 4.7 设置（Settings）

**入口**：菜单「设置」

- **LLM 配置**：API 地址、模型名称、温度、最大 token 数、历史轮数
- **Embedding 配置**：API 地址、模型名称
- **自动归档**：开启/关闭对话自动提炼知识
- **PWA**：支持安装为桌面应用（Service Worker + manifest.json）
- **数据导出**：导出全部知识库 + 报告为 zip 文件

---

## 5. 系统架构

### 5.1 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vue Router + Pinia + Vite |
| 样式 | 自定义 CSS（CSS 变量驱动，支持深色/浅色主题） |
| 后端 | Python 3.11 + FastAPI + Uvicorn |
| 数据库 | SQLite（me.db） |
| 向量存储 | ChromaDB（PersistentClient，本地文件） |
| LLM 集成 | OpenAI 兼容 API（Ollama / vLLM / 任何兼容服务） |
| Markdown | Python `markdown` 库 + 前端 `marked` 库 |
| 部署 | Docker + Docker Compose（多阶段构建） |
| PWA | Service Worker（Network First + Cache Fallback） |

### 5.2 目录结构

```
04-APP/
├── backend/
│   ├── main.py              # FastAPI 应用（单文件，2400+ 行）
│   ├── requirements.txt     # Python 依赖
│   └── Dockerfile           # 多阶段构建（前端 + 后端）
├── frontend/
│   ├── src/
│   │   ├── App.vue          # 根组件（布局、主题、会话管理）
│   │   ├── main.ts          # 入口（路由定义 + 组件预加载）
│   │   ├── style.css        # 全局样式（CSS 变量）
│   │   ├── types.ts         # TypeScript 类型定义
│   │   └── views/           # 视图组件
│   │       ├── ChatView.vue
│   │       ├── DaobenView.vue
│   │       ├── DaobenDashboardView.vue
│   │       ├── ArchiveView.vue
│   │       ├── ArchiveDetailView.vue
│   │       ├── KnowledgeDetailView.vue
│   │       ├── ReportView.vue
│   │       ├── SkillsView.vue
│   │       ├── ExpertConfigView.vue
│   │       ├── ExpertEditView.vue
│   │       ├── SettingsView.vue
│   │       └── UploadsView.vue
│   ├── public/              # PWA 静态资源
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml       # 本地构建部署
├── remote-docker-compose.yml # NAS 远程构建部署
├── README.md
└── .gitignore
```

### 5.3 数据流

```
                  HTTP (6868)
浏览器 ◄────────────────────────► FastAPI
                                      │
                  /api/chat           │        /api/knowledge
                      │               │              │
                      ▼               │              ▼
              ┌──────────────┐        │     ┌──────────────┐
              │  LLM 调用    │◄───────┘     │  ChromaDB    │
              │  (Ollama等)  │              │  (Embedding)  │
              └──────────────┘              └──────────────┘
                      │                            │
                      ▼                            ▼
              ┌──────────────┐           ┌──────────────┐
              │  conversations│           │knowledge_entries│
              │  handoffs     │           │  daoben_entries │
              │  sessions    │           │  reports       │
              └──────────────┘           └──────────────┘
                      │                            │
                      └──────────┬─────────────────┘
                                 ▼
                        ┌──────────────┐
                        │   SQLite     │
                        │   (me.db)    │
                        └──────────────┘
```

---

## 6. 数据模型

### 6.1 数据库表（SQLite）

**conversations** — 对话记录
| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增 |
| session_id | TEXT | 会话 ID |
| role | TEXT | user / assistant / expert |
| content | TEXT | 消息内容 |
| expert_id | TEXT | 回复的专家 ID |

**knowledge_entries** — 知识条目
| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | UUID |
| theme_main | TEXT | 领域主题 |
| summary | TEXT | 摘要 |
| original_text | TEXT | 原始文本 |
| expert_id | TEXT | 来源专家 |
| embedding_id | TEXT | ChromaDB 向量 ID |
| created_at | TEXT | 创建时间 |

**daoben_entries** — 道痕条目
| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | UUID |
| event_text | TEXT | 事件描述 |
| first_reaction | TEXT | 第一反应 |
| greed | TEXT | 贪梦 |
| fear | TEXT | 恐惧 |
| excuses | TEXT | 自洽借口 |
| main_stone | TEXT | 心石 |
| tomorrow_plan | TEXT | 下次计划 |
| source | TEXT | manual / auto |

**reports** — 复盘报告
| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | 时间戳 ID |
| filename | TEXT | HTML 文件名 |
| created_at | TEXT | 生成时间 |

**sessions** — 会话
| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | session_xxx |
| label | TEXT | 会话名称 |
| updated_at | TEXT | 最后活跃时间 |

**settings** — 系统配置
| 字段 | 类型 | 说明 |
|---|---|---|
| key | TEXT PK | 配置键 |
| value | TEXT | 配置值 |

**skills** — 技能注册
| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | 技能目录名 |
| name | TEXT | 显示名 |
| has_manifest | INTEGER | 是否有 SKILL.md |
| enabled | INTEGER | 是否启用 |

**handoffs** — 专家交接
| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | UUID |
| session_id | TEXT | 会话 ID |
| from_expert_id | TEXT | 来源专家 |
| to_expert_id | TEXT | 目标专家 |
| summary | TEXT | 交接摘要 |
| issue | TEXT | 核心问题 |
| context | TEXT | 上下文 |

**experts** — 专家配置
| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | 专家 ID |
| name | TEXT | 名称 |
| avatar | TEXT | 头像 emoji |
| domain | TEXT | 领域 |
| summon_phrase | TEXT | 召唤语 |
| response_phrase | TEXT | 回应语 |
| is_enabled | INTEGER | 是否启用 |
| system_prompt_file | TEXT | 人格文件路径 |

### 6.2 文件存储

| 路径 | 内容 |
|---|---|
| `me_data/me.db` | SQLite 主数据库 |
| `me_data/skills/me_experts/{id}.md` | 专家人格文件 |
| `me_data/skills/{skill_id}/SKILL.md` | 技能定义 |
| `chroma_data/` | ChromaDB 持久化文件 |
| `reports/review-{id}.html` | 复盘报告 HTML |
| `reports/weekly-{id}.html` | 周报 HTML |
| `data/uploads/` | 用户上传文件 |

---

## 7. API 接口

### 7.1 对话
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/chat | 发送消息（支持 summon/auto/handoff） |
| GET | /api/history | 获取对话历史（?session_id=xxx&limit=200） |
| POST | /api/sessions | 创建新会话 |
| GET | /api/sessions | 会话列表 |
| PUT | /api/sessions/{id} | 重命名会话 |
| DELETE | /api/session/{id} | 删除会话及所有消息 |

### 7.2 知识库
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/knowledge/entries | 知识条目列表（?limit=50&theme=xxx&search=xxx） |
| GET | /api/knowledge/entries/{id} | 条目详情 |
| PUT | /api/knowledge/entries/{id} | 编辑条目 |
| DELETE | /api/knowledge/entries/{id} | 删除条目 |
| DELETE | /api/knowledge/clear | 清空知识库 |

### 7.3 道痕
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/daoben/entries | 道痕列表（?search=&limit=50&offset=0） |
| GET | /api/daoben/entries/{id} | 道痕详情 |
| POST | /api/daoben/entries | 创建道痕 |
| DELETE | /api/daoben/entries/{id} | 删除道痕 |
| GET | /api/daoben/stats | 心石统计 |
| GET | /api/daoben/dashboard | 仪表盘数据（?period=week|month|all） |

### 7.4 报告
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/reports | 报告列表 |
| GET | /api/reports/{id} | 查看报告 HTML |
| POST | /api/reports/generate | 生成报告 |
| DELETE | /api/reports/{id} | 删除报告 |

### 7.5 专家
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/experts | 专家列表 |
| GET | /api/experts/{id} | 专家详情（含人格文件内容） |
| POST | /api/experts | 创建/更新专家 |
| PUT | /api/experts/{id} | 更新专家配置 |
| POST | /api/experts/{id}/reset | 重置默认人格 |

### 7.6 技能
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/skills | 技能列表（含描述） |
| PUT | /api/skills/{id} | 启用/停用 |
| POST | /api/skills/upload | 上传技能包（.zip） |
| DELETE | /api/skills/{id} | 删除技能（删除文件 + 记录） |

### 7.7 系统
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/config | 获取配置 |
| PUT | /api/config | 更新配置（写入 settings 表） |
| POST | /api/upload | 上传文件 |
| GET | /api/uploads | 上传文件列表 |
| GET | /api/uploads/{filename} | 下载上传文件 |
| DELETE | /api/uploads/{filename} | 删除上传文件 |
| GET | /api/models | 获取模型列表 |
| GET | /api/export | 导出全部数据为 .zip |
| GET | /health | 健康检查 |

---

## 8. 部署方案

### 8.1 Docker（推荐）

**NAS / 服务器一键部署**：

```yaml
# docker-compose.yml
services:
  me:
    build:
      context: https://github.com/Metruee/Me.git
      dockerfile: backend/Dockerfile
    container_name: me
    environment:
      - LLM_API_BASE=http://ollama:11434/v1
      - LLM_MODEL=qwen2.5:7b
      - EMBEDDING_API_BASE=http://ollama:11434/v1
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

Docker 多阶段构建自动处理：`node:20 编译前端 → python:3.11 装依赖 → 打包启动`。

### 8.2 本地开发

```bash
cd 04-APP/backend && pip install -r requirements.txt && python main.py
cd 04-APP/frontend && npm install && npm run dev
```

### 8.3 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| ME_HOME | /app/me_data | 数据根目录 |
| ME_APP_ROOT | ME_HOME 上级 | 应用根目录 |
| ME_STATIC_DIR | /app/static | 前端静态文件目录 |
| LLM_API_BASE | http://192.168.1.100:11434/v1 | LLM API 地址 |
| LLM_MODEL | (空) | LLM 模型名 |
| EMBEDDING_API_BASE | 同 LLM_API_BASE | Embedding API 地址 |
| EMBEDDING_MODEL | text-embedding-bge-m3 | Embedding 模型名 |
| SKILLS_DIR | ME_HOME/skills | 技能目录 |

### 8.4 升级 & 数据安全

- 数据全部通过 Docker volumes 映射到宿主机目录，容器重建不丢失
- 升级：`docker compose down && docker compose up -d --build`
- 备份：直接复制 `me_data/`、`reports/`、`chroma_data/`、`data/` 目录

---

## 9. 路线图

### 已完成

- [x] 八位专家对话 + 召唤/自动路由/交接
- [x] 多会话管理（创建/切换/重命名/删除）
- [x] 道痕日记（六层捞石头 + 心石统计 + 回看仪表盘）
- [x] 知识库（输入 + 检索 + ChromaDB 语义搜索）
- [x] 复盘报告（知识库 + 道痕 + 历史报告综合分析）
- [x] 技能系统（插件化、.zip 上传、工具注册）
- [x] LLM function calling（web_search、web_fetch + 技能工具）
- [x] 专家人格可编辑（Markdown 文件 + 前端编辑器）
- [x] PWA 支持（Service Worker + manifest）
- [x] Docker 多阶段构建 + 一键部署
- [x] 深色/浅色主题切换
- [x] 对话历史持久化 + 刷新恢复
- [x] 页面 chunk 预加载

### 计划中

- [ ] 定期自动报告（周报/月报定时生成）
- [ ] 专家间对话（多专家对同一问题给出不同视角）
- [ ] 道痕与知识库交叉分析（看"记录的石头"和"写下的知识"的差距）
- [ ] 小说解构（上传完整作品，逆向提取世界观/角色/大纲）
- [ ] 更多数据源（浏览器历史、日历、健康数据接入）
- [ ] 移动端适配优化
- [ ] 国际化（英文版）
- [ ] 预构建 Docker 镜像推送到 GitHub Container Registry

### 待评估

- [ ] 语音输入
- [ ] 情绪曲线可视化（基于道痕数据）
- [ ] 多人共享模式（家庭/团队自知）

---

## 附录：技能开发指南

### SKILL.md 格式

```yaml
---
name: "my-skill"
description: "技能描述"
tools:
  - name: "my_tool"
    description: "工具描述"
    parameters:
      type: object
      properties:
        query:
          type: string
          description: "参数说明"
      required: ["query"]
    handler: "web_search"  # 内置 handler: web_search / web_fetch
---

# 技能正文（Markdown，供专家参考）
```

### 技能打包

将技能文件夹打包为 `.zip`（文件夹名 = 技能 ID），在上传区拖入即可安装。

---

*自知者明，自胜者强。*
