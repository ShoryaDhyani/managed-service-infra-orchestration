import React, { useEffect, useState, useRef } from "react";
import { wsUrlForChannel } from "../api";

export default function LogsPanel({ channel }) {
  const [lines, setLines] = useState([]);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!channel) return;
    const url = wsUrlForChannel(channel);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setLines((prev) => [...prev, `Connected to ${channel}`]);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        const log = data.log || e.data;
        setLines((prev) => [...prev, String(log)]);
      } catch {
        setLines((prev) => [...prev, e.data]);
      }
    };
    ws.onerror = () => setLines((prev) => [...prev, "WebSocket error"]);
    ws.onclose = () => setLines((prev) => [...prev, "Connection closed"]);

    return () => {
      try {
        ws.close();
      } catch {}
    };
  }, [channel]);

  function clear() {
    setLines([]);
  }

  return (
    <div className="logs-panel">
      <div className="logs-header">
        <h3>Live Build Logs</h3>
        <button onClick={clear} className="btn">
          clear
        </button>
      </div>
      <div className="logs-container">
        {lines.map((l, i) => (
          <div key={i} className="log-line">
            {l}
          </div>
        ))}
      </div>
    </div>
  );
}
