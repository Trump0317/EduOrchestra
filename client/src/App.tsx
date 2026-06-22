import { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [backendStatus, setBackendStatus] = useState<string>("checking...");

  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status))
      .catch(() => setBackendStatus("unreachable"));
  }, []);

  return (
    <div className="app">
      <h1>EduOrchestra</h1>
      <p>多智能体驱动的 K12 数学自主学习系统</p>
      <p className="status">
        Backend:{" "}
        <span
          className={
            backendStatus === "ok" ? "ok" : "error"
          }
        >
          {backendStatus}
        </span>
      </p>
    </div>
  );
}

export default App;
