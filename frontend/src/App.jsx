import React, { useState, useEffect } from "react";
import DeployForm from "./components/DeployForm";
import ResultCard from "./components/ResultCard";
import LogsPanel from "./components/LogsPanel";
import DeploymentsList from "./components/DeploymentsList";

export default function App() {
  const [result, setResult] = useState(null);
  const [logsChannel, setLogsChannel] = useState(null);
  const [deployments, setDeployments] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem("deployments") || "[]");
    } catch {
      return [];
    }
  });

  useEffect(() => {
    sessionStorage.setItem("deployments", JSON.stringify(deployments));
  }, [deployments]);

  function handleDeployed(data) {
    setResult(data);
    const slug = data.projectSlug;
    setDeployments((prev) => [
      ...prev,
      {
        slug,
        url: data.url,
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
    setLogsChannel(`logs:${slug}`);
  }

  return (
    <div className="app-shell">
      {/* Top bar */}
      <header className="topbar">
        <div className="topbar-brand">
          <span className="brand-dot" />
          <span className="brand-name">Deploy</span>
        </div>
        <span className="topbar-meta">
          {deployments.length} deployment{deployments.length !== 1 ? "s" : ""}
        </span>
      </header>

      {/* Two-column layout */}
      <main className="layout">
        <div className="panel-left">
          <p className="section-eyebrow">New deployment</p>
          <DeployForm onDeployed={handleDeployed} />
          {result && <ResultCard result={result} />}
        </div>

        <div className="panel-right">
          <LogsPanel channel={logsChannel} />
          <section className="history-section">
            <p className="section-eyebrow">Recent deployments</p>
            <DeploymentsList items={deployments} />
          </section>
        </div>
      </main>
    </div>
  );
}