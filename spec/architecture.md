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
│  │  ├── prompt.py   Prompt 模板引擎       │  │
│  │  └── agents/     Agent 节点            │  │
│  │      ├── assistant.py  ← 全局主管      │  │
│  │      ├── resource.py   ← 学习资料      │  │
│  │      └── practice.py   ← 出题+判题     │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

**图结构** (v0.5)：

```
assistant → resource → practice(中断) → assistant → decide
    ↑                                                    │
    └──────────── next / repeat ─────────────────────────┘
                                                    done → END
```

## 目录结构

```
eduorchestra/
├── spec/                     ← 规格说明书
│   ├── index.md overview.md architecture.md
│   ├── workflow.md testing.md commit.md
│   ├── versions.md
│   └── versions/
│       └── v0.1.md, v0.2.md, v0.3.md, v0.4.md, v0.5.md, v0.6.md
├── server/                   ← Python 后端
│   ├── main.py               ← FastAPI 入口
│   ├── config.py             ← 配置管理
│   ├── routers/              ← API 路由
│   │   ├── __init__.py
│   │   ├── config.py         ← 配置 API
│   │   └── task.py           ← 学习任务 API
│   ├── orchestrator/         ← LangGraph 状态图 + LLM
│   │   ├── state.py          ← AgentState
│   │   ├── graph.py          ← 图编排 + 条件路由
│   │   ├── llm.py            ← LLM 客户端
│   │   ├── tools.py          ← 外部工具（搜索等，v0.6+）
│   │   ├── prompt.py         ← Prompt 模板引擎
│   │   └── agents/           ← Agent 节点
│   │       ├── assistant.py  ← 全局主管（v0.5）
│   │       ├── resource.py   ← 学习资料推荐
│   │       └── practice.py   ← 出题 + 判题
│   ├── demo.py               ← CLI 交互演示
│   └── tests/                ← 后端测试
│       ├── conftest.py
│       ├── unit/
│       │   ├── test_config.py
│       │   ├── test_llm.py
│       │   ├── test_prompt.py
│       │   └── test_graph_structure.py
│       └── integration/
│           ├── test_health.py
│           ├── test_config_api.py
│           ├── test_task_api.py
│           ├── test_workflow.py
│           ├── test_assistant.py
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
│   │   ├── assistant.md
│   │   └── resource.md
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
