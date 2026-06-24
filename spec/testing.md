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
# server/tests/unit/test_graph_structure.py
# 判题逻辑（合并在 test_graph_structure.py 中）
from orchestrator.agents.practice import check_answer, Question

def test_check_answer_correct():
    q: Question = {"id": "q1", "content": "", "options": [],
                   "answer": "B", "kp": ""}
    assert check_answer(q, "B") is True

def test_check_answer_wrong():
    q: Question = {"id": "q1", "content": "", "options": [],
                   "answer": "B", "kp": ""}
    assert check_answer(q, "A") is False
```

### 状态图结构

```python
# server/tests/unit/test_graph_structure.py
from orchestrator.graph import build_graph

def test_graph_has_all_nodes():
    graph = build_graph()
    nodes = list(graph.get_graph().nodes.keys())
    for name in ("assistant", "resource", "practice"):
        assert name in nodes

def test_graph_edge_chain():
    graph = build_graph()
    edges = list(graph.get_graph().edges)
    assert ("resource", "practice") in edges or any(
        src == "resource" and dst == "practice" for src, dst, *_ in edges
    )

def test_graph_interrupts_before_practice():
    graph = build_graph()
    assert "practice" in (graph.interrupt_after_nodes or [])
```

## 集成测试

每个 Agent 调真实 LLM，断言输出结构：

```python
# server/tests/integration/test_assistant.py
# 调真实 LLM，断言返回结构
from orchestrator.agents.assistant import assistant_node

def test_assistant_creates_plan():
    """Assistant 首次调用 → 返回 plan + action=next"""
    state = {
        "task_id": "test-planner",
        "task_goal": "掌握二次函数",
        "plan": [],
        "current_step": 0,
        "step_history": [],
        "resources": [],
        "questions": [],
        "waiting_for_answer": False,
        "answers": [],
        "feedback": None,
        "next_action": "",
    }
    result = assistant_node(state)
    assert "plan" in result
    assert isinstance(result["plan"], list)
    assert len(result["plan"]) >= 1
    assert "title" in result["plan"][0]
    assert "desc" in result["plan"][0]
    assert result["next_action"] == "next"
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
    assert len(state["questions"]) > 0

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
            "question_id": state["questions"][0]["id"],
            "student_answer": "B",
            "is_correct": True,
            "correct_answer": "B"
        }],
        "waiting_for_answer": False,
    })
    state = graph.invoke(None, config)

    # 断言跑到了反馈
    assert state["feedback"] is not None
    assert state["next_action"] in ("repeat", "next")
```

## Chat 集成测试（v0.6+）

> Chat Agent 尚未实现，以下为预留测试设计。

```python
# server/tests/integration/test_chat.py（预留）
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
│   └── test_graph_structure.py  ← 状态图节点+边 + 判题逻辑 + Agent 单元测试
├── integration/
│   ├── __init__.py
│   ├── test_assistant.py        ← Assistant + LLM
│   ├── test_resource.py         ← Resource + LLM
│   ├── test_workflow.py         ← 状态图分段流转
│   ├── test_health.py           ← 健康检查 API
│   ├── test_config_api.py       ← 配置 API
│   └── test_task_api.py         ← 学习任务 API
```
