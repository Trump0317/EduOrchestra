# 测试策略

> 状态：v0.7

## 测试分层

```
        /\
       /E2E\         <- 少量：启动服务，模拟完整学习流程
      /------\
     /Integration\   <- 中量：单个 Agent + LLM 集成，状态图分段运行
    /------------\
   /  Unit Tests  \  <- 大量：状态图结构、Practice 判题、工具函数
  /________________\
```

## 各层策略

| 层级 | 范围 | 策略 | 框架 |
|------|------|------|------|
| 单元测试 | 判题逻辑、状态图结构、工具函数 | 不调 LLM，纯逻辑 / Mock | pytest |
| 集成测试 | 单个 Agent + 真实 LLM | 调真实 LLM，断言结构而非内容 | pytest |
| E2E 测试 | 完整状态图流转 | 调真实 LLM，分段 invoke | 手动 / pytest |

---

## 测试原则

- **真实 LLM**：Agent 集成测试调真实 LLM，不 mock。因为 mock 返回值无法验证 prompt 质量
- **断言结构**：不断言 LLM 输出内容（每次可能不同），只断言输出格式和字段存在
- **分段 invoke**：Practice 节点有 interrupt，测试时分段运行状态图
- **独立验证**：每个 Agent 可独立测试，不依赖其他 Agent 的前置执行

## 单元测试

针对不调 LLM 的纯逻辑：

### Practice 判题逻辑

```python
# server/tests/unit/test_graph_structure.py
from orchestrator.agents.practice import check_answer

def test_check_answer_correct():
    q = {"id": "q1", "content": "", "options": [],
         "answer": "B", "kp": ""}
    assert check_answer(q, "B") is True

def test_check_answer_wrong():
    q = {"id": "q1", "content": "", "options": [],
         "answer": "B", "kp": ""}
    assert check_answer(q, "A") is False
```

### 状态图结构（v0.7：五节点）

```python
# server/tests/unit/test_graph_structure.py
from orchestrator.graph import build_graph

def test_graph_has_all_nodes():
    graph = build_graph()
    nodes = list(graph.get_graph().nodes.keys())
    for name in ("planner", "assistant", "resource", "practice", "diagnose"):
        assert name in nodes

def test_graph_edge_chain():
    graph = build_graph()
    edges = list(graph.get_graph().edges)
    edge_pairs = [
        ("resource", "practice"),
        ("practice", "diagnose"),
        ("diagnose", "assistant"),
    ]
    for src, dst in edge_pairs:
        assert (src, dst) in edges or any(
            e[0] == src and e[1] == dst for e in edges
        )

def test_graph_interrupts_before_practice():
    graph = build_graph()
    assert "practice" in (graph.interrupt_after_nodes or [])
```

### 搜索工具（v0.6+）

```python
# server/tests/unit/test_tools.py
from orchestrator.tools import build_search_query, search_resources

def test_build_search_query():
    result = build_search_query("二次函数", "学习定义")
    assert "二次函数" in result
    assert "高一数学" in result

def test_search_resources_error_handling():
    # Mock 异常 → 返回空列表
    with patch("orchestrator.tools.DDGS", side_effect=Exception):
        assert search_resources("test") == []
```

## 集成测试

每个 Agent 调真实 LLM，断言输出结构：

### Planner 集成测试（v0.7+）

```python
# server/tests/integration/test_planner.py
from orchestrator.agents.planner import planner_node

def test_planner_creates_plan():
    state = {"task_id": "test", "task_goal": "掌握二次函数", ...}
    result = planner_node(state)
    assert "plan" in result
    assert 2 <= len(result["plan"]) <= 5
    assert "title" in result["plan"][0]
```

### Assistant 集成测试（v0.7+）

```python
# server/tests/integration/test_assistant.py
from orchestrator.agents.assistant import assistant_node

def test_assistant_routes_first_call():
    """有计划无 feedback → action=next"""
    state = make_state(plan=[...], feedback=None)
    result = assistant_node(state)
    assert result["next_action"] == "next"
```

### Diagnose 集成测试（v0.7+）

```python
# server/tests/integration/test_feedback.py
from orchestrator.agents.feedback import feedback_node

def test_feedback_returns_diagnosis():
    state = make_state(answers=[...])
    result = feedback_node(state)
    fb = result["feedback"]
    assert "summary" in fb
    assert "strengths" in fb
    assert "weaknesses" in fb
```

### 状态图分段测试

```python
# server/tests/integration/test_workflow.py
from orchestrator.graph import build_graph

def test_workflow_to_practice():
    """状态图应跑到 Practice 节点暂停"""
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-1"}}
    state = graph.invoke({"task_goal": "掌握二次函数", "task_id": "test"}, config)
    assert state["waiting_for_answer"] is True
    assert len(state["questions"]) > 0
```

## Chat 集成测试（v0.8+）

> Chat Agent 尚未实现，以下为预留测试设计。

```python
# server/tests/integration/test_chat.py（预留）
from orchestrator.agents.chat import chat_response

def test_chat_with_task_context():
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
├── conftest.py                  ← 全局 fixtures（预留）
├── unit/
│   ├── __init__.py
│   ├── test_config.py           ← 配置管理
│   ├── test_llm.py              ← LLM 客户端
│   ├── test_prompt.py           ← Prompt 模板引擎
│   ├── test_tools.py            ← 搜索工具 (v0.6+)
│   └── test_graph_structure.py  ← 状态图节点+边 + 判题逻辑 + Agent 单元测试
├── integration/
│   ├── __init__.py
│   ├── test_assistant.py        ← Assistant 路由 (v0.7: 重构)
│   ├── test_planner.py          ← Planner (v0.7+)
│   ├── test_feedback.py         ← Diagnose (v0.7+)
│   ├── test_resource.py         ← Resource + LLM + 搜索
│   ├── test_workflow.py         ← 状态图分段流转
│   ├── test_health.py           ← 健康检查 API
│   ├── test_config_api.py       ← 配置 API
│   └── test_task_api.py         ← 学习任务 API
```
