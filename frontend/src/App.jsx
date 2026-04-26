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
      { slug, url: data.url, time: new Date().toLocaleString() },
    ]);
    setLogsChannel(`logs:${slug}`);
  }

  return (
    <div className="container">
      <header>
        <h1>Deploy</h1>
      </header>

      <main>
        <DeployForm onDeployed={handleDeployed} />
        {result && <ResultCard result={result} />}
        <LogsPanel channel={logsChannel} />
        <section className="recent">
          <h2>Recent Deployments</h2>
          <DeploymentsList items={deployments} />
        </section>
      </main>
    </div>
  );
}
