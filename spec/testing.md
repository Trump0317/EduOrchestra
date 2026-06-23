# 测试策略

> 状态：v0.2 设计期

## 测试分层

```
        /\
       /E2E\         <- 少量：启动服务，模拟完整学习流程
      /------\
     /Integration\   <- 中量：单个 Agent + LLM 集成，状态图分段运行
    /------------\
   /  Unit Tests  \  <- 大量：状态图结构、Practice 判题逻辑
  /________________\
```

## 各层策略

| 层级 | 范围 | 策略 | 框架 |
|------|------|------|------|
| 单元测试 | Practice 判题、状态图结构断言 | 不调 LLM，纯逻辑测试 | pytest |
| 集成测试 | 单个 Agent + 真实 LLM | 调真实 LLM，断言结构而非内容 | pytest |
| E2E 测试 | 完整状态图流转 | 调真实 LLM，分段 invoke | 手动 / pytest |

---

## 测试原则

- **真实 LLM**：Agent 集成测试调真实 LLM，不 mock。因为 mock 返回值无法验证 prompt 质量
- **断言结构**：不断言 LLM 输出内容（每次可能不同），只断言输出格式和字段存在
- **分段 invoke**：Practice 节点有 interrupt，测试时分段运行状态图

## 单元测试

针对不调 LLM 的纯逻辑：

### Practice 判题逻辑

```python
# server/tests/unit/test_practice.py
# 测试 Practice Agent 的判题和题目读取逻辑
from orchestrator.agents.practice import check_answer, load_questions

def test_load_questions_by_kp():
    """根据知识点 ID 加载题目"""
    questions = load_questions(["kp-2-1"])
    assert len(questions) > 0
    assert all("content" in q for q in questions)

def test_check_answer_correct():
    question = {"answer": "B"}
    assert check_answer(question, "B") is True

def test_check_answer_wrong():
    question = {"answer": "B"}
    assert check_answer(question, "A") is False
```

### 状态图结构

```python
# server/tests/unit/test_graph_structure.py
from orchestrator.graph import build_graph

def test_graph_has_all_nodes():
    graph = build_graph()
    nodes = graph.get_graph().nodes.keys()
    assert "planner" in nodes
    assert "resource" in nodes
    assert "practice" in nodes
    assert "analytics" in nodes
    assert "feedback" in nodes

def test_graph_starts_from_planner():
    graph = build_graph()
    edges = graph.get_graph().edges
    # 有从 START 到 planner 的边
    assert ("__start__", "planner") in edges or any(
        src == "__start__" for src, _, _ in edges
    )
```

## 集成测试

每个 Agent 调真实 LLM，断言输出结构：

```python
# server/tests/integration/test_planner.py
# 调真实 LLM，断言返回结构
from orchestrator.agents.planner import planner_node
from orchestrator.state import AgentState

def test_planner_returns_steps():
    """Planner Agent 应返回步骤序列"""
    state = {"task_goal": "掌握二次函数"}
    result = planner_node(state)
    assert "plan" in result
    assert isinstance(result["plan"], list)
    assert len(result["plan"]) >= 1
    assert "title" in result["plan"][0]
    assert "desc" in result["plan"][0]
```

### 状态图分段测试

```python
# server/tests/integration/test_workflow.py
# 分段 invoke 状态图，验证流转逻辑
from orchestrator.graph import build_graph

def test_workflow_to_practice():
    """状态图应跑到 Practice 节点暂停"""
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-1"}}

    state = graph.invoke(
        {"task_goal": "掌握二次函数", "task_id": "test-task"},
        config
    )
    # 断言跑到了 Practice 并等待答案
    assert state["waiting_for_answer"] is True
    assert len(state["current_questions"]) > 0

def test_workflow_resume_after_answer():
    """提交答案后状态图应继续流转"""
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-2"}}

    # 第一段：跑到 Practice
    state = graph.invoke(
        {"task_goal": "掌握二次函数", "task_id": "test-task"},
        config
    )
    # 注入答案并 resume
    graph.update_state(config, {
        "answers": [{
            "question_id": state["current_questions"][0]["id"],
            "student_answer": "B",
            "is_correct": True,
            "correct_answer": "B"
        }],
        "waiting_for_answer": False,
    })
    state = graph.invoke(None, config)

    # 断言跑到了反馈
    assert "feedback" in state
    assert "analytics" in state
```

## Chat 集成测试

```python
# server/tests/integration/test_chat.py
from orchestrator.agents.chat import chat_response

def test_chat_with_task_context():
    """Chat 应能够基于任务上下文回答问题"""
    response = chat_response(
        message="二次函数的对称轴怎么求？",
        context={"task_goal": "掌握二次函数", "current_step": 1}
    )
    assert isinstance(response, str)
    assert len(response) > 0
```

## 测试目录结构

```
server/tests/
├── conftest.py                  ← 全局 fixtures
├── unit/
│   ├── __init__.py
│   ├── test_practice.py         ← 判题逻辑、题目加载
│   └── test_graph_structure.py  ← 状态图节点和边
├── integration/
│   ├── __init__.py
│   ├── test_planner.py          ← Planner + LLM
│   ├── test_resource.py         ← Resource + LLM
│   ├── test_analytics.py        ← Analytics + LLM
│   ├── test_feedback.py         ← Feedback + LLM
│   ├── test_workflow.py         ← 状态图分段流转
│   └── test_chat.py             ← Chat + LLM
└── e2e/
    └── test_full_flow.py        ← 完整学习循环
```
