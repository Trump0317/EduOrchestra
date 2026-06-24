# 项目概述

## 项目定位

EduOrchestra 是一个**多智能体协作的模拟课堂**，面向高一学生数学自主学习。系统充当 AI 学习伙伴：学生设定学习任务，5 个 AI Agent 协作完成计划制定、资源搜集、做题练习、学情诊断和智能路由，Assistant 配备 Tool Calling 能力（搜索、记忆读写）。

## 设计理念

- **预置题库 + 后期拓展**：MVP 预置少量 JSON 题目，后续版本加入 AI 题目生成
- **学生直接使用**：单用户本地模式，浏览器打开即用
- **LangGraph 状态图编排**：5 个 Agent 作为状态图节点，各司其职，Practice 节点暂停等待学生输入
- **Tool Calling**：Assistant 可自主调用 4 个工具（search_web / fetch_page / save_memory / read_memory）获取信息和记录记忆
- **真实 LLM 驱动**：4 个 Agent 调真实 LLM（Practice 除外），Prompt 与代码分离

## 核心交互流程

```
学生创建任务（如"掌握二次函数"）
           │
           ▼
    Planner: 拆解为步骤序列 + 制定学习路径
           │
           ▼
    Assistant: 读全局状态做路由决策 → 开始学习
           │
           ▼
    Resource: 为当前步骤搜集学习资料（DuckDuckGo 真实搜索）
           │
           ▼
    Practice:  从题库出题 → 等待学生提交答案(⏸)
           │         逐题判对错，记录答案
           ▼
    Diagnose: 分析答题表现 → 诊断报告（含 strengths/weaknesses）
           │
           ▼
    Assistant: 读全局状态 + feedback → 智能路由决策
           │
           ├─ repeat: 重新学习当前步骤 → Resource
           ├─ next:   进入下一步         → Resource
           └─ done:   全部完成           → 任务结束
```

## Agent 概览

| Agent | 职责 | LLM | 数据依赖 |
|-------|------|:---:|---------|
| **Planner** | 拆解学习目标 → 2-5 步计划 | ✅ | task_goal |
| **Assistant** | 读全局状态 → 智能路由决策 + Tool Calling（4 工具） | ✅ | plan, feedback, step_history, answers |
| Resource | DuckDuckGo 搜索 + LLM 富化推荐学习资料 | ✅ | 当前步骤信息 |
| Practice | 从题库出题 + 判对错 | ❌ | 题库 JSON |
| **Diagnose** | 分析答题表现 → 诊断报告（summary/strengths/weaknesses/suggestion） | ✅ | answers, step_history |
