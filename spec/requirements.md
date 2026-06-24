# EduOrchestra 需求文档

> 状态：v0.9 完成 | 日期：2026-06-24

---

## 1. 项目定位

EduOrchestra 是一个**多智能体协作的模拟课堂**，面向 K12 学生自主学习场景。学生设定学习任务（目标），多个 AI Agent 协作完成：制定计划 → 搜集学习资料 → 出题练习 → 学情诊断 → 反馈报告，并根据反馈自动调整计划。

**核心理念**：AI 学习伙伴——既能在学生迷茫时给出方向，又能在学生有明确目标时辅助拆解执行。

---

## 2. 用户与场景

### 2.1 目标用户

| 维度 | 定位 |
|------|------|
| **学段** | MVP 聚焦 **高一数学** |
| **学科** | 先做数学，验证后扩展 |
| **核心使用者** | 学生（直接操作，自主使用） |

### 2.2 使用场景

| 场景 | 描述 |
|------|------|
| **课后自学巩固** | 学生放学后自主使用，查漏补缺 |
| **目标驱动学习** | 学生设定目标（如"掌握二次函数"），系统拆解任务 |

### 2.3 交互形态

- **结构化任务流**：创建任务 → 自动流转（计划 → 资源 → 做题 → 诊断 → 反馈 → 调整），做题节点暂停等待学生提交
- **对话式**：侧边常驻 Chat，学生随时提问，AI 携带当前任务上下文回答

---

## 3. 核心功能

### 3.1 制定计划（Planner Agent）

- 学生设定学习目标（自然语言）→ LLM 拆解为 2-5 个步骤序列
- 每个步骤含 title（步骤名）和 desc（学习内容与标准）

### 3.2 资源搜集（Resource Agent）

- DuckDuckGo 真实搜索 + LLM 过滤富化推荐学习资料
- 输出：视频链接、文章链接、知识点标签、内容描述

### 3.3 做题练习（Practice 节点）

- 从预置题库读取与当前步骤关联的题目
- 逐题展示，学生提交答案后实时判对错
- 记录答题结果（题号、学生答案、是否正确）

### 3.4 答题诊断（Diagnose Agent）

- LLM 分析答题表现 → 生成诊断报告
- 输出：summary（整体评价）、strengths（掌握点）、weaknesses（薄弱点）、suggestion（建议）

### 3.5 智能路由（Assistant Agent）

- LLM 读取全局状态（plan + feedback + step_history + answers）→ 智能路由决策
- 路由: repeat（重学当前步）/ next（进入下一步）/ done（全部完成）
- 输出决策理由（reason），体现教学考量而非机械公式

---

## 4. 多智能体架构

### 4.1 Agent 角色定义

| Agent | 职责 | LLM | 数据依赖 |
|-------|------|:---:|---------|
| **Planner** | 拆解学习目标 → 步骤计划 | ✅ | task_goal |
| **Assistant** | 读全局状态 → 智能路由决策（含 Tool Calling：search_web / fetch_page / save_memory / read_memory） | ✅ | plan, feedback, step_history, answers, 长期记忆 |
| **Resource** | DuckDuckGo 搜索 + LLM 富化推荐资料 | ✅ | 当前步骤信息 |
| **Practice** | 从题库出题 + 判对错 | ❌ | 题库 |
| **Diagnose** | 分析答题表现 → 诊断报告 | ✅ | answers, step_history |
| **Chat** | 对话辅导（独立，v0.8+） | ✅ | 当前任务上下文（预留） |

### 4.2 编排方式

LangGraph 状态图管理流转： Planner → Assistant → Resource → Practice → Diagnose → Assistant 循环。
Practice 节点暂停（interrupt）等待学生提交答案，Diagnose 在答题后自动触发诊断，Assistant 在 Planner 之后和 Diagnose 之后各被调用一次做路由决策。

Assistant 配备 Tool Calling 能力：可在决策前调用 search_web / fetch_page 获取外部信息，调用 read_memory / save_memory 读写长期记忆。

### 4.3 记忆系统（v0.9+）

两层记忆，全部 JSON 文件存储：
- **短期记忆**：`data/tasks/{id}.json` — 任务完成时自动归档完整状态快照
- **长期记忆**：`data/memories.json`（键值记忆）+ `data/profile.json`（用户画像）

Assistant 通过 Tool Calling 读写长期记忆，任务完成时自动提炼画像。

### 4.3 状态管理

MVP 阶段使用 LangGraph MemorySaver（内存），暂不持久化。后续版本引入 SQLite checkpoint。

---

## 5. 技术方案

### 5.1 技术栈

| 层 | 技术选型 |
|----|---------|
| 后端语言 | Python 3.12+ |
| 多智能体框架 | LangGraph（状态图编排） |
| LLM | ChatOpenAI（OpenAI-compatible 协议，含 DeepSeek） |
| Web 框架 | FastAPI |
| 前端 | React 18 + Vite（分步页面已完成） |
| 题库 | JSON 文件（预置 3 道题，后续扩展） |

### 5.2 Prompt 管理

Prompt 模板存放在 `data/prompts/` 目录，与代码分离，便于调优。

### 5.3 架构概述

```
┌─ LangGraph 状态图（MemorySaver）──────────────┐
│                                                │
│  Planner ──→ Assistant ──→ Resource ──→ Practice(⏸)
│  (LLM)        (LLM 路由)    (LLM+搜索)    (题库+判题)
│                  ↑                            │
│                  └──── Diagnose ←─────────────┘
│                        (LLM 诊断)              │
│                                                │
└────────────────────────────────────────────────┘
                   ↑ 共享上下文 (AgentState)
┌─ 侧边 ──────────┴─────────────────────────────┐
│  Chat (LLM, 独立端点, v0.8+)                   │
└────────────────────────────────────────────────┘
```

---

## 6. MVP 范围

### 6.1 目标

验证核心链路：**目标 → 计划 → 资源 → 做题 → 诊断 → 反馈 → 调整**

### 6.2 范围界定

| 维度 | MVP 范围 |
|------|---------|
| **学段** | 高一数学（先覆盖 1-2 个知识点） |
| **Agent** | 5 个 Agent（Planner / Assistant / Resource / Practice / Diagnose），4 个 LLM 驱动 |
| **题库** | 预置 3 道 JSON 题目（后续扩展） |
| **搜索** | DuckDuckGo 真实搜索 + LLM 过滤富化（v0.6+） |
| **交互** | 做题节点暂停，学生提交答案后继续流转 |
| **前端** | React + Vite 分步页面（plan → resource → practice → result） |
| **状态** | 内存（MemorySaver），重启丢失 |
| **用户** | 单用户本地模式 |

### 6.3 不做什么（MVP）

- 不做 SQLite 持久化
- 不做 AI 题目生成
- 不做知识图谱
- 不做用户认证

---

## 7. 变更记录

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-06-22 | 初稿，完成需求访谈 | AI + 用户 |
| 2026-06-23 | v0.2 重构：聚焦后端 + LangGraph 状态图 + 真实 LLM + 内存状态 | AI + 用户 |
| 2026-06-24 | v0.6：新增 DuckDuckGo 真实搜索 + Resource 资料富化 | AI + 用户 |
| 2026-06-24 | v0.9：记忆系统（JSON）+ Tool Calling 基础设施（search_web / fetch_page / save_memory / read_memory） | AI + 用户 |
