# 架构设计

## 技术选型

| 层 | 技术 | 理由 |
|----|------|------|
| 后端语言 | Python 3.12+ | AI/LLM 生态最成熟 |
| 多智能体框架 | LangGraph | 状态图编排、checkpoint、interrupt |
| Web 框架 | FastAPI | 异步原生、自动 OpenAPI |
| 前端 | React 18 + Vite | 生态最大，适合复杂交互 |
| AI 接口 | 云端 API（DeepSeek / OpenAI） | 效果好、省心 |

## 架构图

```
┌──────────────────────────────────────────────┐
│            Browser (localhost:5173)           │
│  ┌────────────────────────────────────────┐  │
│  │           React 前端 (Vite)            │  │
│  │  分步页面: 计划 → 资料 → 做题 → 反馈  │  │
│  └────────────────┬───────────────────────┘  │
│                   │ REST                      │
└───────────────────┼──────────────────────────┘
                    │
┌───────────────────▼──────────────────────────┐
│           FastAPI 服务层 (端口 8000)          │
│  ┌────────────────────────────────────────┐  │
│  │  main.py      应用入口                 │  │
│  │  config.py    配置管理（.env）         │  │
│  │  routers/      API 路由                │  │
│  │  ├── config.py   GET/PUT /api/config   │  │
│  │  └── task.py     POST/GET /api/task    │  │
│  └────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────┐  │
│  │  orchestrator/   LangGraph 状态图      │  │
│  │  ├── state.py    AgentState 定义       │  │
│  │  ├── graph.py    图编排 + 条件路由     │  │
│  │  ├── llm.py      LLM 客户端封装        │  │
│  │  ├── tools.py     LangChain 工具集 + 搜索 │  │
│  │  ├── prompt.py   Prompt 模板引擎       │  │
│  │  └── agents/     Agent 节点 (5)        │  │
│  │      ├── planner.py     ← 制定计划 (LLM)   │  │
│  │      ├── assistant.py  ← 智能路由 + Tool Calling │  │
│  │      ├── resource.py   ← 学习资料 (LLM)   │  │
│  │      ├── practice.py   ← 出题+判题         │  │
│  │      └── feedback.py   ← 答题诊断 (LLM)   │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

**图结构** (v0.8)：

```
planner → assistant ─┬─ next/repeat → resource → practice → diagnose → assistant
            ↑        ├─ done → END                                  │
            │        └─ replan ─────────────────────────────────────┘
            └────────────────────────────────────────────────────────┘
```

- Planner: 初始规划 / 动态重规划（双模式）
- Assistant: 智能路由（next / repeat / done / replan）
- Diagnose: 答题诊断 → Assistant 读取 feedback 判断是否需要 replan

## 目录结构

```
eduorchestra/
├── spec/                     ← 规格说明书
│   ├── index.md overview.md architecture.md
│   ├── workflow.md testing.md commit.md
│   ├── versions.md
│   └── versions/
│       └── v0.1.md ~ v0.9.md
├── server/                   ← Python 后端
│   ├── main.py               ← FastAPI 入口
│   ├── config.py             ← 配置管理
│   ├── memory.py             ← 记忆系统 (JSON) (v0.9+)
│   ├── routers/              ← API 路由
│   │   ├── __init__.py
│   │   ├── config.py         ← 配置 API
│   │   ├── task.py           ← 学习任务 API
│   │   └── progress.py       ← 学习进度 API (v0.9+)
│   ├── orchestrator/         ← LangGraph 状态图 + LLM
│   │   ├── state.py          ← AgentState
│   │   ├── graph.py          ← 图编排 + 条件路由
│   │   ├── llm.py            ← LLM 客户端
│   │   ├── tools.py          ← 搜索 + LangChain Tools (v0.9+)
│   │   ├── prompt.py         ← Prompt 模板引擎
│   │   └── agents/           ← Agent 节点 (5)
│   │       ├── planner.py    ← 制定学习计划 (v0.7)
│   │       ├── assistant.py  ← 智能路由 + Tool Calling (v0.9+)
│   │       ├── resource.py   ← 学习资料推荐
│   │       ├── practice.py   ← 出题 + 判题
│   │       └── feedback.py   ← 答题诊断 (v0.7)
│   ├── demo.py               ← CLI 交互演示
│   └── tests/                ← 后端测试
│       ├── conftest.py
│       ├── unit/
│       │   ├── test_config.py
│       │   ├── test_llm.py
│       │   ├── test_prompt.py
│       │   ├── test_tools.py
│       │   ├── test_memory.py     ← v0.9+
│       │   └── test_graph_structure.py
│       └── integration/
│           ├── test_health.py
│           ├── test_config_api.py
│           ├── test_task_api.py
│           ├── test_workflow.py
│           ├── test_assistant.py
│           ├── test_planner.py
│           ├── test_feedback.py
│           └── test_resource.py
├── client/                   ← React 前端
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       └── App.css
├── data/                     ← 运行时数据
│   ├── prompts/              ← Prompt 模板
│   │   ├── planner.md
│   │   ├── assistant.md
│   │   ├── resource.md
│   │   └── feedback.md
├── .env.example
├── pyproject.toml
└── README.md
```

## API 端点清单

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/config` | 获取配置（LLM provider/model） |
| PUT | `/api/config` | 更新配置 |

### 学习任务（v0.4+）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/task` | 创建任务 + 首次 invoke |
| GET | `/api/task/{task_id}` | 查询任务状态 |
| POST | `/api/task/{task_id}/answer` | 提交答案 + resume 图 |

### 学习进度（v0.9+）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/progress` | 学习进度总览 |
| GET | `/api/progress/topics` | 已学知识点列表 |
| GET | `/api/progress/tasks` | 历史任务列表 |
