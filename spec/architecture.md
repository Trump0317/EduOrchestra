# 架构设计

## 技术选型

| 层 | 技术 | 理由 |
|----|------|------|
| 后端语言 | Python 3.12+ | AI/LLM 生态最成熟，LangGraph 原生支持 |
| 多智能体框架 | LangGraph | 状态图编排、checkpoint、human-in-the-loop，生产级 |
| Web 框架 | FastAPI | 异步原生、自动 OpenAPI、SSE 支持好 |
| 前端 | React 18 + Vite | 生态最大，组件库丰富，适合复杂交互 |
| 数据库 (MVP) | SQLite | 零配置，单用户本地场景足够 |
| AI 接口 | 云端 API（DeepSeek / OpenAI / Claude） | 效果好、省心 |

## 技术不选型

| 不选 | 原因 |
|------|------|
| CrewAI / AutoGen | 偏对话式协作，Orchestrator 调度场景 LangGraph 更合适 |
| TypeScript 全栈 | 多智能体框架 Python-first，混用增加复杂度 |
| Vue | 用户偏好 React |
| PostgreSQL (MVP) | MVP 单用户本地，SQLite 够用，生产再切 |
| Streamlit/Gradio | AI 原型虽快，但复杂交互（答题面板+对话+报告）hold 不住 |

## 架构图

```
┌──────────────────────────────────────────────┐
│            Browser (localhost:5173)           │
│  ┌────────────────────────────────────────┐  │
│  │           React 前端 (Vite)            │  │
│  │  App.tsx                               │  │
│  │  ├── Dashboard   目标 + 任务面板       │  │
│  │  ├── AnswerView  答题界面              │  │
│  │  ├── ChatView    对话辅导界面          │  │
│  │  └── ReportView  学情报告面板          │  │
│  └────────────────┬───────────────────────┘  │
│                   │ REST + SSE                │
└───────────────────┼──────────────────────────┘
                    │
┌───────────────────▼──────────────────────────┐
│           FastAPI 服务层 (端口 8000)          │
│  ┌────────────────────────────────────────┐  │
│  │  routers/                              │  │
│  │  ├── questions.py  题库 CRUD           │  │
│  │  ├── practice.py   答题 + 判题         │  │
│  │  ├── analytics.py  学情查询            │  │
│  │  ├── plans.py      目标 + 计划         │  │
│  │  ├── chat.py       对话辅导            │  │
│  │  └── knowledge.py  知识图谱            │  │
│  └────────────────┬───────────────────────┘  │
└───────────────────┼──────────────────────────┘
                    │
┌───────────────────▼──────────────────────────┐
│          Agent 层 (LangGraph)                 │
│  ┌────────────────────────────────────────┐  │
│  │  orchestrator/                         │  │
│  │  ├── graph.py         状态图定义       │  │
│  │  ├── state.py         共享状态         │  │
│  │  └── agents/                           │  │
│  │      ├── resource.py  资源搜集 Agent   │  │
│  │      ├── analytics.py 学情分析 Agent   │  │
│  │      ├── feedback.py  反馈生成 Agent   │  │
│  │      ├── planner.py   计划制定 Agent   │  │
│  │      └── tutor.py     对话辅导 Agent   │  │
│  └────────────────┬───────────────────────┘  │
└───────────────────┼──────────────────────────┘
                    │
┌───────────────────▼──────────────────────────┐
│            数据层 (SQLite)                    │
│  ┌────────────────────────────────────────┐  │
│  │  models/                               │  │
│  │  ├── question.py     题库模型          │  │
│  │  ├── knowledge.py    知识图谱模型      │  │
│  │  ├── practice.py     答题记录模型      │  │
│  │  ├── plan.py         目标+计划模型     │  │
│  │  └── chat.py         对话历史模型      │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

## 目录结构

```
eduorchestra/
├── spec/                     ← 规格说明书
│   ├── index.md overview.md architecture.md
│   ├── workflow.md testing.md commit.md
│   └── versions.md versions/
├── server/                   ← Python 后端
│   ├── main.py               ← FastAPI 入口
│   ├── config.py             ← 配置管理
│   ├── database.py           ← SQLAlchemy engine + session
│   ├── models/               ← 数据模型
│   │   ├── __init__.py
│   │   ├── question.py
│   │   ├── knowledge.py
│   │   ├── practice.py
│   │   ├── plan.py
│   │   └── chat.py
│   ├── routers/              ← API 路由
│   │   ├── __init__.py
│   │   ├── questions.py
│   │   ├── practice.py
│   │   ├── analytics.py
│   │   ├── plans.py
│   │   ├── chat.py
│   │   └── knowledge.py
│   ├── orchestrator/         ← LangGraph 编排层
│   │   ├── __init__.py
│   │   ├── graph.py          ← 状态图定义
│   │   ├── state.py          ← AgentState 共享状态
│   │   └── agents/           ← 各 Agent 实现
│   │       ├── __init__.py
│   │       ├── resource.py
│   │       ├── analytics.py
│   │       ├── feedback.py
│   │       ├── planner.py
│   │       └── tutor.py
│   ├── services/             ← 业务逻辑层
│   │   ├── __init__.py
│   │   ├── question_gen.py   ← AI 题目生成
│   │   ├── exam_import.py    ← 高考真题导入
│   │   └── llm.py            ← LLM 调用封装
│   └── tests/                ← 后端测试
│       ├── __init__.py
│       ├── conftest.py
│       ├── unit/
│       │   └── __init__.py
│       └── integration/
│           └── __init__.py
├── client/                   ← React 前端
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   └── src/
│       ├── main.tsx App.tsx App.css
│       ├── pages/
│       │   ├── Dashboard.tsx
│       │   ├── AnswerView.tsx
│       │   ├── ChatView.tsx
│       │   └── ReportView.tsx
│       ├── components/
│       │   ├── QuestionCard.tsx
│       │   ├── ChatBubble.tsx
│       │   └── KnowledgeMap.tsx
│       ├── hooks/
│       │   ├── usePractice.ts
│       │   ├── useChat.ts
│       │   └── useAnalytics.ts
│       └── api/
│           └── client.ts     ← API 请求封装
├── data/                     ← 运行时数据
│   ├── mock/                 ← Mock 数据（v0.2-v0.8）
│   │   ├── knowledge.json    ← 知识点 mock
│   │   └── questions.json    ← 题目 mock
│   └── eduorchestra.db       ← SQLite 数据库（v0.9+）
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 核心模块接口

### AgentState (orchestrator/state.py)

所有 Agent 共享的状态定义：

```python
from typing import TypedDict, List, Optional
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    """Orchestrator 共享状态"""
    # 学生信息
    student_id: str
    # 当前目标
    current_goal: Optional[str]
    goal_knowledge_points: List[str]  # 目标关联知识点ID列表
    # 答题会话
    active_practice: Optional[dict]   # 当前答题会话
    practice_results: List[dict]      # 本轮答题结果
    # 学情分析
    weak_points: List[dict]           # 薄弱知识点列表
    knowledge_heatmap: dict           # 知识掌握热力图
    # 计划
    task_sequence: List[dict]         # 拆解后的任务序列
    current_task_index: int
    # 反馈
    feedback_messages: List[str]
    weekly_report: Optional[str]
    # 流程控制
    next_step: str  # 下一步要执行的操作
```

### 状态图 (orchestrator/graph.py)

```python
from langgraph.graph import StateGraph, START, END
from orchestrator.state import AgentState
from orchestrator.agents import (
    resource_agent, analytics_agent, feedback_agent,
    planner_agent, tutor_agent
)

def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("planner", planner_agent)
    builder.add_node("resource", resource_agent)
    builder.add_node("practice", practice_router)   # 路由到前端答题
    builder.add_node("analytics", analytics_agent)
    builder.add_node("feedback", feedback_agent)
    builder.add_node("tutor", tutor_agent)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "resource")
    builder.add_edge("resource", "practice")
    builder.add_edge("practice", "analytics")
    builder.add_conditional_edges(
        "analytics",
        decide_next,
        {
            "feedback": "feedback",
            "planner": "planner",   # 需要调整计划
            "tutor": "tutor",       # 学生提问
            "practice": "practice", # 继续做题
        }
    )
    builder.add_edge("feedback", END)
    builder.add_edge("tutor", "analytics")

    return builder.compile()
```

### LLM 调用封装 (services/llm.py)

```python
from openai import AsyncOpenAI

class LLMService:
    """统一的 LLM 调用封装，支持多 Provider"""
    def __init__(self, provider: str, api_key: str, model: str):
        base_urls = {
            "deepseek": "https://api.deepseek.com",
            "openai": "https://api.openai.com/v1",
            "claude": "https://api.anthropic.com",
        }
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_urls.get(provider, base_urls["openai"])
        )
        self.model = model

    async def chat(self, messages: list, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content

    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """生成结构化 JSON 输出"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(response.choices[0].message.content)
```

### 数据模型 (models/question.py)

```python
from sqlalchemy import Column, Integer, String, Text, Enum
from database import Base

class Question(Base):
    __tablename__ = "questions"

    id: int = Column(Integer, primary_key=True, index=True)
    content: str = Column(Text, nullable=False)          # 题干 (LaTeX)
    question_type: str = Column(String(20), default="single_choice")
    # single_choice | multi_choice | fill_in_blank | detailed_answer
    answer: str = Column(Text, nullable=False)           # 正确答案
    explanation: str = Column(Text, default="")          # 解析
    difficulty: str = Column(String(10), default="medium")
    # easy | medium | hard
    knowledge_points: str = Column(Text, default="[]")   # JSON: ["kp_id1", "kp_id2"]
    source: str = Column(String(50), default="ai_gen")   # ai_gen | exam_import
    created_at: str = Column(String(30))
```

## API 端点清单

### 题库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/questions` | 题目列表（支持知识点、难度、题型筛选） |
| GET | `/api/questions/{id}` | 题目详情 |
| POST | `/api/questions/generate` | AI 生成题目 |
| POST | `/api/questions/import` | 导入高考真题 |

### 答题

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/practice/start` | 开始答题会话（指定知识点/目标） |
| GET | `/api/practice/next` | 获取下一题 |
| POST | `/api/practice/submit` | 提交答案 |
| GET | `/api/practice/result/{session_id}` | 答题会话结果 |

### 学情

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/analytics/weak-points` | 薄弱知识点列表 |
| GET | `/api/analytics/heatmap` | 知识掌握热力图 |
| GET | `/api/analytics/report/weekly` | 周报告 |

### 计划

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/plans/goal` | 设定学习目标 |
| GET | `/api/plans/tasks` | 获取当前任务序列 |
| PUT | `/api/plans/tasks/{id}/complete` | 完成任务 |

### 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 发送消息（非流式） |
| GET | `/api/chat/stream` | SSE 流式对话 |

### 知识图谱

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/tree` | 知识点树 |
| GET | `/api/knowledge/{id}` | 知识点详情（含前置依赖） |

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/config` | 获取配置（LLM provider/model） |
| PUT | `/api/config` | 更新配置 |

## 数据流 — 一次完整学习循环

```
学生设定目标 "掌握二次函数"
    │
    ▼
POST /api/plans/goal  →  Planner Agent
    │                        │
    │                   LLM 拆解目标:
    │                   1. 二次函数定义与图像
    │                   2. 二次函数性质
    │                   3. 二次函数应用题
    │                        │
    ▼                        ▼
Resource Agent ← 按知识点生成/匹配题目
    │
    ▼
POST /api/practice/start  →  开始答题
    │
    ├── GET /api/practice/next  →  显示题目
    ├── POST /api/practice/submit  →  提交答案
    │       │
    │       ▼
    │   Analytics Agent: 实时分析（更新知识图谱状态）
    │   Feedback Agent: 生成即时反馈
    │       │
    │       ▼
    │   前端显示: ✓/✗ + 解析 + 知识点提醒
    │
    └── ... 重复直到任务完成
            │
            ▼
    Analytics Agent: 薄弱点诊断
    Feedback Agent: 生成本轮学习报告
            │
            ▼
   学生查看报告 → 设定新目标 or 对话提问
```
