# 测试策略

## 测试分层

```
        /\
       /E2E\         <- 少量：启动完整服务，浏览器验证核心流程
      /------\
     /Integration\   <- 中量：FastAPI 路由 + Agent mock
    /------------\
   /  Unit Tests  \  <- 大量：模型、服务函数、Agent 逻辑
  /________________\
```

## 各层策略

| 层级 | 范围 | Mock 策略 | 框架 |
|------|------|----------|------|
| 单元测试 | 单个函数、模型方法 | mock LLM 调用、数据库操作 | pytest |
| 集成测试 | FastAPI 路由 + 数据库 | mock LLM 调用 | pytest + httpx |
| E2E 测试 | 启动服务 + 浏览器 | 真实 LLM 或 mock | 手动 / Playwright (后续) |

## 后端测试

### 单元测试

```python
# server/tests/unit/test_question_gen.py
# 测试行为：
# - test_generate_question_returns_structured_data: 输入合法知识点，返回含核心字段的结构化题目
# - test_generate_question_handles_empty_knowledge: 空知识点时返回空列表
# - test_generate_question_validates_llm_output: LLM 返回缺字段时，校验器拦截
import pytest
from unittest.mock import AsyncMock, patch
from services.question_gen import QuestionGenerator

@pytest.mark.asyncio
async def test_generate_question_returns_structured_data():
    """AI 题目生成应返回符合核心字段的结构化数据"""
    gen = QuestionGenerator(llm_service=mock_llm)

    result = await gen.generate(knowledge_point="二次函数定义")

    assert "content" in result
    assert "answer" in result
    assert "explanation" in result
    assert result["difficulty"] in ("easy", "medium", "hard")
```

### Mock 数据 Fixture

```python
# server/tests/conftest.py
import json, pytest
from pathlib import Path

@pytest.fixture
def mock_knowledge():
    """加载 mock 知识点数据"""
    path = Path(__file__).parent.parent / "data" / "mock" / "knowledge.json"
    return json.loads(path.read_text())

@pytest.fixture
def mock_questions():
    """加载 mock 题目数据"""
    path = Path(__file__).parent.parent / "data" / "mock" / "questions.json"
    return json.loads(path.read_text())
```

### 集成测试

```python
# server/tests/integration/test_practice_api.py
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_start_practice_and_submit():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 开始答题
        resp = await client.post("/api/practice/start", json={
            "knowledge_points": ["kp_quadratic_func"]
        })
        assert resp.status_code == 200
        session_id = resp.json()["session_id"]

        # 获取题目
        resp = await client.get(f"/api/practice/next?session_id={session_id}")
        assert resp.status_code == 200
        question = resp.json()

        # 提交答案
        resp = await client.post("/api/practice/submit", json={
            "session_id": session_id,
            "question_id": question["id"],
            "answer": question["answer"],  # 正确答案
            "time_spent": 45
        })
        assert resp.status_code == 200
        assert resp.json()["correct"] is True
```

## 前端测试

前端 UI 组件不写自动化测试，采用开发服务器 + 浏览器手动验证：

1. `cd client && npm run dev`
2. 开发者在浏览器中查看
3. 反馈修改意见 → 修改 → 刷新浏览器

## Mock 策略

```python
# LLM mock: 返回预设 JSON，避免调真实 API
mock_llm = AsyncMock()
mock_llm.generate_json.return_value = {
    "content": r"已知函数 $f(x) = x^2 + 2x + 1$，求 $f(3)$ 的值。",
    "answer": "16",
    "explanation": "将 x=3 代入: f(3) = 3^2 + 2×3 + 1 = 9 + 6 + 1 = 16",
    "knowledge_points": ["kp_quadratic_func"],
    "difficulty": "easy"
}

# 数据库 mock: 使用 SQLite 内存数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
```

## 测试目录结构

```
server/tests/
├── conftest.py              ← 全局 fixtures、mock 工厂
├── unit/
│   ├── test_question_gen.py ← AI 题目生成
│   ├── test_exam_import.py  ← 真题导入
│   ├── test_knowledge.py    ← 知识图谱逻辑
│   ├── test_analytics.py    ← 学情分析逻辑
│   ├── test_feedback.py     ← 反馈生成逻辑
│   ├── test_tutor.py        ← 对话辅导逻辑
│   └── test_planner.py      ← 计划拆解逻辑
├── integration/
│   ├── test_questions_api.py
│   ├── test_practice_api.py
│   ├── test_analytics_api.py
│   ├── test_plans_api.py
│   └── test_chat_api.py
└── e2e/                     ← 后续添加
```
