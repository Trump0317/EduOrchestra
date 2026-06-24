import { useState } from "react";
import "./App.css";

/* ── TypeScript ── */

interface TaskState {
  task_id: string;
  task_goal: string;
  status: "waiting_for_answer" | "completed";
  plan: { title: string; desc: string }[];
  current_step: number;
  resources: { type: string; title: string; url: string; description?: string; knowledge_points?: string[] }[];
  questions: { id: string; content: string; options: string[]; kp: string }[];
  feedback: { summary: string; suggestion: string } | null;
  next_action: string;  // "next" | "repeat" | "done" | "replan"
  step_history: { step_index: number; rounds: number; best_accuracy: number; latest_accuracy: number }[];
}

type Phase = "idle" | "loading" | "plan" | "resource" | "practice" | "result";

/* ── 子组件 ── */

function Spinner({ text }: { text: string }) {
  return (
    <div className="spinner">
      <div className="spinner-icon" />
      <p>{text}</p>
    </div>
  );
}

function StepDots({ current, plan }: { current: number; plan: TaskState["plan"] }) {
  return (
    <div className="step-dots">
      {plan.map((_, i) => (
        <div
          key={i}
          className={`dot ${i < current ? "done" : i === current ? "active" : ""}`}
        />
      ))}
    </div>
  );
}

/* ── Idle ── */
function GoalForm({ onSubmit }: { onSubmit: (goal: string) => void }) {
  const [goal, setGoal] = useState("");
  return (
    <form
      className="card center"
      onSubmit={(e) => {
        e.preventDefault();
        if (goal.trim()) onSubmit(goal.trim());
      }}
    >
      <h2>🎯 你想学什么？</h2>
      <p className="hint">输入一个高一数学知识点</p>
      <input
        type="text"
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        placeholder="例如：掌握二次函数"
        autoFocus
      />
      <button type="submit" disabled={!goal.trim()}>开始学习</button>
    </form>
  );
}

/* ── Plan ── */
function PlanView({ plan, onStart }: { plan: TaskState["plan"]; onStart: () => void }) {
  return (
    <div className="card center">
      <h2>📋 学习计划</h2>
      <p className="hint">助手已将目标拆解为 {plan.length} 个步骤</p>
      <ol className="plan-list">
        {plan.map((s, i) => (
          <li key={i}>
            <span className="plan-num">{i + 1}</span>
            <div>
              <strong>{s.title}</strong>
              <p>{s.desc}</p>
            </div>
          </li>
        ))}
      </ol>
      <button onClick={onStart}>开始第一步</button>
    </div>
  );
}

/* ── Resource ── */
function ResourceView({
  taskState,
  onStartPractice,
}: {
  taskState: TaskState;
  onStartPractice: () => void;
}) {
  const step = taskState.plan[taskState.current_step];
  return (
    <>
      <StepDots current={taskState.current_step} plan={taskState.plan} />
      <div className="card center">
        <span className="step-label">
          第 {taskState.current_step + 1} / {taskState.plan.length} 步
        </span>
        <h2>{step?.title}</h2>
        <p className="step-desc">{step?.desc}</p>
      </div>
      <div className="card">
        <h3>📚 学习资料</h3>
        <div className="resource-list">
          {taskState.resources.map((r, i) => (
            <a key={i} href={r.url} target="_blank" rel="noopener noreferrer" className="res-item">
              <span className="res-icon">{r.type === "video" ? "🎬" : "📄"}</span>
              <div className="res-content">
                <span className="res-title">{r.title}</span>
                {r.description && <span className="res-desc">{r.description}</span>}
                {r.knowledge_points && r.knowledge_points.length > 0 && (
                  <div className="res-kps">
                    {r.knowledge_points.map((kp, j) => (
                      <span key={j} className="kp-tag">{kp}</span>
                    ))}
                  </div>
                )}
              </div>
            </a>
          ))}
        </div>
      </div>
      <button onClick={onStartPractice}>开始做题</button>
    </>
  );
}

/* ── Practice ── */
function PracticeView({
  taskState,
  selected,
  onChange,
  onSubmit,
}: {
  taskState: TaskState;
  selected: Record<string, string>;
  onChange: (id: string, val: string) => void;
  onSubmit: () => void;
}) {
  const allAnswered = taskState.questions.every((q) => selected[q.id]);
  const step = taskState.plan[taskState.current_step];
  return (
    <>
      <StepDots current={taskState.current_step} plan={taskState.plan} />
      <div className="card center">
        <span className="step-label">
          第 {taskState.current_step + 1} / {taskState.plan.length} 步
        </span>
        <h2>{step?.title}</h2>
      </div>
      <div className="card">
        <h3>✏️ 练习题</h3>
        {taskState.questions.map((q) => (
          <div key={q.id} className="q-item">
            <p className="q-text">{q.content}</p>
            <div className="opts">
              {q.options.map((opt) => {
                const letter = opt.charAt(0);
                return (
                  <label key={letter} className={`opt ${selected[q.id] === letter ? "sel" : ""}`}>
                    <input type="radio" name={q.id} value={letter}
                      checked={selected[q.id] === letter}
                      onChange={() => onChange(q.id, letter)} />
                    <span>{opt}</span>
                  </label>
                );
              })}
            </div>
          </div>
        ))}
        <button onClick={onSubmit} disabled={!allAnswered}>提交答案</button>
      </div>
    </>
  );
}

/* ── Result ── */
function ResultView({
  taskState,
  onContinue,
  onRestart,
}: {
  taskState: TaskState;
  onContinue: () => void;
  onRestart: () => void;
}) {
  const { feedback, plan, current_step, next_action, step_history } = taskState;
  const lastRecord = step_history?.[step_history.length - 1];
  const totalSteps = plan.length;

  return (
    <>
      {lastRecord && (
        <div className="card center">
          <h3>📊 答题结果</h3>
          <div className="stats">
            <div className="stat">
              <span className="stat-val">{(lastRecord.latest_accuracy * 100).toFixed(0)}%</span>
              <span className="stat-lbl">正确率</span>
            </div>
            <div className="stat">
              <span className="stat-val">{lastRecord.rounds}</span>
              <span className="stat-lbl">第几轮</span>
            </div>
          </div>
        </div>
      )}

      {feedback && (
        <div className="card center">
          <h3>💬 助手反馈</h3>
          <p className="fb-summary">{feedback.summary}</p>
          <p className="fb-suggestion">{feedback.suggestion}</p>
        </div>
      )}

      <div className="card center">
        {next_action === "next" && current_step < totalSteps ? (
          <>
            <p className="action-hint">进入下一步</p>
            <p className="next-preview"><strong>{plan[current_step]?.title}</strong></p>
            <button onClick={onContinue}>查看学习资料</button>
          </>
        ) : next_action === "repeat" ? (
          <>
            <p className="action-hint">正确率不够，再学一次</p>
            <button onClick={onContinue}>重新学习</button>
          </>
        ) : next_action === "replan" ? (
          <>
            <p className="action-hint">学习计划需要调整，正在重新规划...</p>
            <button onClick={onContinue}>查看新计划</button>
          </>
        ) : (
          <>
            <h3>🎉 全部完成！</h3>
            <p>已完成全部 {totalSteps} 个步骤</p>
            <button onClick={onRestart}>再来一次</button>
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
  const [selected, setSelected] = useState<Record<string, string>>({});
  const [loadingMsg, setLoadingMsg] = useState("");

  async function apiCall(url: string, body?: object): Promise<TaskState | null> {
    try {
      const resp = await fetch(url, {
        method: body ? "POST" : "GET",
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return await resp.json();
    } catch (err) {
      alert("请求失败，请检查后端是否启动");
      setPhase("idle");
      return null;
    }
  }

  async function handleStart(goal: string) {
    setLoadingMsg("助手正在制定学习计划...");
    setPhase("loading");
    const state = await apiCall("/api/task", { goal });
    if (state) {
      setTaskState(state);
      setPhase("plan");
    }
  }

  function handleBeginStep() {
    setPhase("resource");
  }

  function handleStartPractice() {
    setPhase("practice");
  }

  async function handleSubmit() {
    if (!taskState) return;
    const answers = Object.entries(selected).map(([qid, ans]) => ({
      question_id: qid,
      student_answer: ans,
    }));
    setLoadingMsg("助手正在分析...");
    setPhase("loading");
    const state = await apiCall(`/api/task/${taskState.task_id}/answer`, { answers });
    if (state) {
      setTaskState(state);
      setSelected({});
      setPhase("result");
    }
  }

  function handleContinue() {
    if (!taskState) return;
    if (taskState.next_action === "repeat") {
      // 重新学习当前步骤 → 回到做题
      setPhase("practice");
    } else {
      // next 或 done → 看资料
      setPhase("resource");
    }
  }

  function handleRestart() {
    setTaskState(null);
    setSelected({});
    setPhase("idle");
  }

  return (
    <div className="app">
      <header>
        <h1>EduOrchestra</h1>
        <p className="subtitle">多智能体驱动的 K12 数学自主学习</p>
      </header>

      <main>
        {phase === "idle" && <GoalForm onSubmit={handleStart} />}

        {phase === "loading" && <Spinner text={loadingMsg} />}

        {phase === "plan" && taskState && (
          <PlanView plan={taskState.plan} onStart={handleBeginStep} />
        )}

        {phase === "resource" && taskState && (
          <ResourceView taskState={taskState} onStartPractice={handleStartPractice} />
        )}

        {phase === "practice" && taskState && (
          <PracticeView
            taskState={taskState}
            selected={selected}
            onChange={(id, val) => setSelected((p) => ({ ...p, [id]: val }))}
            onSubmit={handleSubmit}
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

      <footer>EduOrchestra v0.6</footer>
    </div>
  );
}

export default App;
