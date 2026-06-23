# 架构设计

## 技术选型

| 层 | 技术 | 理由 |
|----|------|------|
| 后端语言 | Python 3.12+ | AI/LLM 生态最成熟 |
| Web 框架 | FastAPI | 异步原生、自动 OpenAPI |
| 前端 | React 18 + Vite | 生态最大，适合复杂交互 |
| AI 接口 | 云端 API（DeepSeek / OpenAI） | 效果好、省心 |

## 架构图

```
┌──────────────────────────────────────────────┐
│            Browser (localhost:5173)           │
│  ┌────────────────────────────────────────┐  │
│  │           React 前端 (Vite)            │  │
│  │  App.tsx                               │  │
│  │  └── 健康检查 + 配置展示               │  │
│  └────────────────┬───────────────────────┘  │
│                   │ REST                      │
└───────────────────┼──────────────────────────┘
                    │
┌───────────────────▼──────────────────────────┐
│           FastAPI 服务层 (端口 8000)          │
│  ┌────────────────────────────────────────┐  │
│  │  main.py    应用入口 + /api/health     │  │
│  │  config.py  配置管理（.env 读取）      │  │
│  │  routers/                              │  │
│  │  └── config.py  GET/PUT /api/config    │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

## 目录结构

```
eduorchestra/
├── spec/                     ← 规格说明书
│   ├── index.md overview.md architecture.md
│   ├── workflow.md testing.md commit.md
│   ├── versions.md
│   └── versions/
│       └── v0.1.md
├── server/                   ← Python 后端
│   ├── __init__.py
│   ├── main.py               ← FastAPI 入口
│   ├── config.py             ← 配置管理
│   ├── routers/              ← API 路由
│   │   ├── __init__.py
│   │   └── config.py         ← 配置 API
│   └── tests/                ← 后端测试
│       ├── __init__.py
│       ├── conftest.py
│       ├── unit/
│       │   ├── __init__.py
│       │   └── test_config.py
│       └── integration/
│           ├── __init__.py
│           ├── test_health.py
│           └── test_config_api.py
├── client/                   ← React 前端
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       └── App.css
├── data/                     ← 运行时数据目录
│   └── mock/                 ← Mock 数据（后续版本使用）
├── requirements.txt
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
