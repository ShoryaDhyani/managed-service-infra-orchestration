import React, { useEffect, useState, useRef } from "react";
import { wsUrlForChannel } from "../api";

function classifyLine(line) {
  const l = line.toLowerCase();
  if (l.includes("error") || l.includes("fail") || l.includes("fatal")) return "error";
  if (l.includes("warn")) return "warn";
  if (
    l.includes("success") ||
    l.includes("done") ||
    l.includes("complete") ||
    l.includes("built") ||
    l.includes("live")
  )
    return "success";
  return "info";
}

export default function LogsPanel({ channel }) {
  const [lines, setLines] = useState([]);
  const wsRef = useRef(null);
  const bodyRef = useRef(null);

  useEffect(() => {
    if (!channel) return;
    const url = wsUrlForChannel(channel);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setLines((prev) => [...prev, `Connected to ${channel}`]);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setLines((prev) => [...prev, String(data.log ?? e.data)]);
      } catch {
        setLines((prev) => [...prev, e.data]);
      }
    };
    ws.onerror = () => setLines((prev) => [...prev, "WebSocket error"]);
    ws.onclose = () => setLines((prev) => [...prev, "Connection closed"]);

    return () => {
      try { ws.close(); } catch {}
    };
  }, [channel]);

  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [lines]);

  return (
    <div className="terminal">
      <div className="terminal-bar">
        <div className="terminal-dots">
          <span className="dot" />
          <span className="dot" />
          <span className="dot" />
        </div>
        <span className="terminal-label">{channel ?? "— no channel —"}</span>
        <button className="terminal-clear" onClick={() => setLines([])}>
          clear
        </button>
      </div>

      <div className="terminal-body" ref={bodyRef}>
        {!channel ? (
          <div className="no-channel-msg">Deploy a project to see live build logs.</div>
        ) : (
          lines.map((line, i) => (
            <div className="log-line" key={i}>
              <span className="log-prefix">{String(i + 1).padStart(3, "0")}</span>
              <span className={`log-text log-${classifyLine(line)}`}>{line}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}