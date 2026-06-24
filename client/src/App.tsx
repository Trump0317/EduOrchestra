import { useState } from "react";
import "./App.css";

/* ── TypeScript ── */

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

type Phase = "idle" | "loading" | "plan" | "step" | "result";

/* ── 子组件 ── */

function Spinner({ text }: { text: string }) {
  return (
    <div className="spinner">
      <div className="spinner-icon" />
      <p>{text}</p>
    </div>
  );
}

/** 步骤进度条 */
function StepProgress({
  current,
  plan,
}: {
  current: number;
  plan: TaskState["plan"];
}) {
  return (
    <div className="step-progress">
      <div className="step-progress-bar">
        {plan.map((_, i) => (
          <div
            key={i}
            className={`step-dot ${i < current ? "done" : i === current ? "active" : ""}`}
          >
            <span>{i + 1}</span>
          </div>
        ))}
      </div>
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
      className="card"
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

function PlanView({
  plan,
  onStart,
}: {
  plan: TaskState["plan"];
  onStart: () => void;
}) {
  return (
    <div className="card">
      <h2>📋 学习计划</h2>
      <p className="hint">AI 已将你的目标拆解为 {plan.length} 个步骤</p>
      <ol className="plan-list">
        {plan.map((step, i) => (
          <li key={i}>
            <span className="plan-step-num">{i + 1}</span>
            <div>
              <strong>{step.title}</strong>
              <p>{step.desc}</p>
            </div>
          </li>
        ))}
      </ol>
      <button onClick={onStart}>开始第一步</button>
    </div>
  );
}

function StepView({
  taskState,
  selectedAnswers,
  onAnswerChange,
  onSubmit,
  loading,
}: {
  taskState: TaskState;
  selectedAnswers: Record<string, string>;
  onAnswerChange: (id: string, answer: string) => void;
  onSubmit: () => void;
  loading: boolean;
}) {
  const { plan, current_step, resources, questions } = taskState;
  const step = plan[current_step];
  const allAnswered = questions.every((q) => selectedAnswers[q.id]);

  return (
    <>
      <StepProgress
        current={current_step}
        plan={plan}
      />

      <div className="card section-title">
        <span className="step-label">
          第 {current_step + 1} / {plan.length} 步
        </span>
        <h2>{step?.title}</h2>
        <p className="step-desc">{step?.desc}</p>
      </div>

      {resources?.length > 0 && (
        <div className="card">
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
      )}

      <div className="card">
        <h3>✏️ 练习题</h3>
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
    </>
  );
}

function ResultView({
  taskState,
  onContinue,
  onRestart,
}: {
  taskState: TaskState;
  onContinue: () => void;
  onRestart: () => void;
}) {
  const { analytics, feedback, plan, current_step, next_action } = taskState;
  const totalSteps = plan.length;
  const done = current_step >= totalSteps && next_action !== "repeat_step";

  return (
    <>
      {analytics && (
        <div className="card result-card">
          <h3>📊 答题结果</h3>
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
              薄弱点：{analytics.weak_points.join("、")}
            </div>
          )}
          {analytics.summary && (
            <p className="summary-text">{analytics.summary}</p>
          )}
        </div>
      )}

      {feedback && (
        <div className="card result-card">
          <h3>💡 反馈</h3>
          <p className="feedback-summary">{feedback.summary}</p>
          <p className="feedback-suggestion">{feedback.suggestion}</p>
        </div>
      )}

      <div className="card action-card">
        {done ? (
          <>
            <h3>🎉 全部完成！</h3>
            <p>已完成全部 {totalSteps} 个步骤</p>
            <button onClick={onRestart}>再来一次</button>
          </>
        ) : next_action === "repeat_step" ? (
          <>
            <p className="action-hint">
              🔄 正确率不够，需要重新学习当前步骤
            </p>
            <button onClick={onContinue}>再做一次</button>
          </>
        ) : (
          <>
            <p className="action-hint">
              ✅ 本步通关，准备进入下一步
            </p>
            {current_step + 1 < totalSteps && (
              <p className="next-step-preview">
                下一步：<strong>{plan[current_step + 1]?.title}</strong>
              </p>
            )}
            <button onClick={onContinue}>
              {current_step + 1 < totalSteps ? "进入下一步" : "继续"}
            </button>
          </>
        )}
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
  const [loadingMsg, setLoadingMsg] = useState("");

  async function handleStart(goal: string) {
    setLoadingMsg("AI 正在生成学习计划...");
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
      setPhase("plan");
    } catch {
      alert("创建任务失败，请检查后端是否启动。");
      setPhase("idle");
    }
  }

  function handleStartStep() {
    setPhase("step");
  }

  function handleAnswerChange(questionId: string, answer: string) {
    setSelectedAnswers((prev) => ({ ...prev, [questionId]: answer }));
  }

  async function handleSubmitAnswers() {
    if (!taskState) return;
    setLoadingMsg("AI 正在分析答题结果...");
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
      setPhase("result");
    } catch {
      alert("提交失败，请重试。");
      setPhase("step");
    }
  }

  function handleContinue() {
    if (!taskState) return;
    setPhase("step");
  }

  function handleRestart() {
    setTaskState(null);
    setSelectedAnswers({});
    setPhase("idle");
  }

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

        {phase === "loading" && <Spinner text={loadingMsg} />}

        {phase === "plan" && taskState && (
          <PlanView plan={taskState.plan} onStart={handleStartStep} />
        )}

        {phase === "step" && taskState && (
          <StepView
            taskState={taskState}
            selectedAnswers={selectedAnswers}
            onAnswerChange={handleAnswerChange}
            onSubmit={handleSubmitAnswers}
            loading={false}
          />
        )}

        {phase === "result" && taskState && (
          <ResultView
            taskState={taskState}
            onContinue={handleContinue}
            onRestart={handleRestart}
          />
        )}
      </main>

      <footer>EduOrchestra v0.4</footer>
    </div>
  );
}

export default App;
