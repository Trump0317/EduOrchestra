import { useState } from "react";
import "./App.css";

/* ── TypeScript 类型 ── */

interface TaskState {
  task_id: string;
  task_goal: string;
  status: "waiting_for_answer" | "completed";
  plan: { title: string; desc: string }[];
  current_step: number;
  resources: { type: string; title: string; url: string }[];
  questions: { id: string; content: string; options: string[]; kp: string }[];
  analytics: Record<string, any> | null;
  feedback: { summary: string; suggestion: string } | null;
  next_action: string;
}

type Phase = "idle" | "loading" | "ready" | "result";

/* ── 子组件 ── */

function Spinner({ text }: { text: string }) {
  return (
    <div className="spinner">
      <div className="spinner-icon" />
      <p>{text}</p>
    </div>
  );
}

function GoalForm({
  onSubmit,
  loading,
}: {
  onSubmit: (goal: string) => void;
  loading: boolean;
}) {
  const [goal, setGoal] = useState("");
  return (
    <form
      className="card goal-form"
      onSubmit={(e) => {
        e.preventDefault();
        if (goal.trim()) onSubmit(goal.trim());
      }}
    >
      <h2>🎯 你想学什么？</h2>
      <p className="hint">输入一个高一数学知识点作为学习目标</p>
      <input
        type="text"
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        placeholder="例如：掌握二次函数"
        disabled={loading}
        autoFocus
      />
      <button type="submit" disabled={loading || !goal.trim()}>
        {loading ? "生成中..." : "开始学习"}
      </button>
    </form>
  );
}

function PlanView({ plan }: { plan: TaskState["plan"] }) {
  return (
    <div className="card section">
      <h3>📋 学习计划</h3>
      <ol className="plan-list">
        {plan.map((step, i) => (
          <li key={i}>
            <strong>{step.title}</strong>
            <p>{step.desc}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}

function ResourcesView({
  resources,
}: {
  resources: TaskState["resources"];
}) {
  if (!resources || resources.length === 0) return null;
  return (
    <div className="card section">
      <h3>📚 学习资料</h3>
      <div className="resource-list">
        {resources.map((r, i) => (
          <a
            key={i}
            href={r.url}
            target="_blank"
            rel="noopener noreferrer"
            className="resource-item"
          >
            <span className="resource-type">
              {r.type === "video" ? "🎬" : "📄"}
            </span>
            <span>{r.title}</span>
          </a>
        ))}
      </div>
    </div>
  );
}

function QuestionPanel({
  questions,
  selectedAnswers,
  onAnswerChange,
  onSubmit,
  loading,
  stepInfo,
}: {
  questions: TaskState["questions"];
  selectedAnswers: Record<string, string>;
  onAnswerChange: (id: string, answer: string) => void;
  onSubmit: () => void;
  loading: boolean;
  stepInfo: string;
}) {
  const allAnswered = questions.every((q) => selectedAnswers[q.id]);
  return (
    <div className="card section">
      <h3>✏️ 答题 — {stepInfo}</h3>
      {questions.map((q) => (
        <div key={q.id} className="question-item">
          <p className="question-text">{q.content}</p>
          <div className="options">
            {q.options.map((opt) => {
              const letter = opt.charAt(0);
              return (
                <label
                  key={letter}
                  className={`option-label ${
                    selectedAnswers[q.id] === letter ? "selected" : ""
                  }`}
                >
                  <input
                    type="radio"
                    name={q.id}
                    value={letter}
                    checked={selectedAnswers[q.id] === letter}
                    onChange={() => onAnswerChange(q.id, letter)}
                    disabled={loading}
                  />
                  <span>{opt}</span>
                </label>
              );
            })}
          </div>
        </div>
      ))}
      <button
        className="submit-btn"
        onClick={onSubmit}
        disabled={!allAnswered || loading}
      >
        {loading ? "提交中..." : "提交答案"}
      </button>
    </div>
  );
}

function ResultView({
  taskState,
  onContinue,
  loading,
}: {
  taskState: TaskState;
  onContinue: () => void;
  loading: boolean;
}) {
  const { analytics, feedback, plan, current_step, next_action } = taskState;
  const totalSteps = plan.length;
  const done = next_action === "" && current_step >= totalSteps;

  return (
    <>
      {analytics && (
        <div className="card section">
          <h3>📊 答题分析</h3>
          <div className="stats">
            <div className="stat">
              <span className="stat-value">
                {analytics.correct_count}/{analytics.total_questions}
              </span>
              <span className="stat-label">正确</span>
            </div>
            <div className="stat">
              <span className="stat-value">
                {(analytics.accuracy * 100).toFixed(0)}%
              </span>
              <span className="stat-label">正确率</span>
            </div>
          </div>
          {analytics.weak_points?.length > 0 && (
            <div className="weak-points">
              <p>薄弱点：{analytics.weak_points.join("、")}</p>
            </div>
          )}
          {analytics.summary && (
            <p className="summary-text">{analytics.summary}</p>
          )}
        </div>
      )}

      {feedback && (
        <div className="card section">
          <h3>💡 反馈与建议</h3>
          <p className="feedback-summary">{feedback.summary}</p>
          <p className="feedback-suggestion">{feedback.suggestion}</p>
        </div>
      )}

      <div className="card section next-step">
        {done ? (
          <>
            <h3>🎉 全部完成！</h3>
            <p>你已经完成了全部 {totalSteps} 个步骤的学习。</p>
          </>
        ) : next_action === "repeat_step" ? (
          <p>🔄 需要重新学习当前步骤，再做一次题吧</p>
        ) : next_action === "next_step" && current_step < totalSteps ? (
          <p>
            ✅ 进入下一步：<strong>{plan[current_step]?.title}</strong>
          </p>
        ) : null}
        <button className="continue-btn" onClick={onContinue} disabled={loading}>
          {done ? "重新开始" : "继续"}
        </button>
      </div>
    </>
  );
}

/* ── 主应用 ── */

function App() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [taskState, setTaskState] = useState<TaskState | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<
    Record<string, string>
  >({});

  async function handleStart(goal: string) {
    setPhase("loading");
    try {
      const resp = await fetch("/api/task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const state: TaskState = await resp.json();
      setTaskState(state);
      setPhase("ready");
    } catch (err) {
      alert("创建任务失败，请检查后端是否启动");
      setPhase("idle");
    }
  }

  function handleAnswerChange(questionId: string, answer: string) {
    setSelectedAnswers((prev) => ({ ...prev, [questionId]: answer }));
  }

  async function handleSubmitAnswers() {
    if (!taskState) return;
    setPhase("loading");
    const answers = Object.entries(selectedAnswers).map(
      ([question_id, student_answer]) => ({ question_id, student_answer })
    );
    try {
      const resp = await fetch(`/api/task/${taskState.task_id}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const state: TaskState = await resp.json();
      setTaskState(state);
      setSelectedAnswers({});
      // 如果还在等待答题 → 显示题目；否则显示结果
      setPhase(state.status === "waiting_for_answer" ? "ready" : "result");
    } catch (err) {
      alert("提交答案失败，请重试");
      setPhase("ready");
    }
  }

  function handleContinue() {
    if (!taskState) {
      setPhase("idle");
      return;
    }
    if (taskState.status === "waiting_for_answer") {
      setPhase("ready");
    } else {
      // 已完成 → 回到首页
      setTaskState(null);
      setSelectedAnswers({});
      setPhase("idle");
    }
  }

  const currentStep =
    taskState?.plan[taskState.current_step]?.title ?? "";

  return (
    <div className="app">
      <header>
        <h1>EduOrchestra</h1>
        <p className="subtitle">多智能体驱动的 K12 数学自主学习</p>
      </header>

      <main>
        {phase === "idle" && (
          <GoalForm onSubmit={handleStart} loading={false} />
        )}

        {phase === "loading" && (
          <Spinner
            text={
              taskState === null
                ? "AI 正在生成学习计划..."
                : "AI 正在分析答题结果..."
            }
          />
        )}

        {phase === "ready" && taskState && (
          <>
            <div className="step-badge">
              第 {taskState.current_step + 1} / {taskState.plan.length} 步
            </div>
            <PlanView plan={taskState.plan} />
            <ResourcesView resources={taskState.resources} />
            <QuestionPanel
              questions={taskState.questions}
              selectedAnswers={selectedAnswers}
              onAnswerChange={handleAnswerChange}
              onSubmit={handleSubmitAnswers}
              loading={false}
              stepInfo={currentStep}
            />
          </>
        )}

        {phase === "result" && taskState && (
          <ResultView
            taskState={taskState}
            onContinue={handleContinue}
            loading={false}
          />
        )}
      </main>

      <footer>
        <p>EduOrchestra v0.4</p>
      </footer>
    </div>
  );
}

export default App;
