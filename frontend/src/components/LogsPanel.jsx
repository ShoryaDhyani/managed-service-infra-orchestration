import React, { useEffect, useState, useRef } from "react";
import { wsUrlForChannel } from "../api";

function classifyLine(line) {
  const l = String(line).toLowerCase();

  if (l.includes("error") || l.includes("fail") || l.includes("fatal")) {
    return "error";
  }
  if (l.includes("warn")) {
    return "warn";
  }
  if (
    l.includes("success") ||
    l.includes("done") ||
    l.includes("complete") ||
    l.includes("built") ||
    l.includes("live")
  ) {
    return "success";
  }
  return "info";
}

export default function LogsPanel({ channel, setDeployments }) {
  const [lines, setLines] = useState([]);
  const bodyRef = useRef(null);

  useEffect(() => {
    if (!channel) return;

    const ws = new WebSocket(wsUrlForChannel(channel));
    const slug = channel.replace("logs:", "");

    ws.onopen = () => {
      setLines((prev) => [...prev, `Connected to ${channel}`]);
    };

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        const log = String(data.log ?? "");

        setLines((prev) => [...prev, log]);

        if (log.toLowerCase() === "failed") {
          setDeployments((prev) =>
            prev.map((d) =>
              d.slug === slug ? { ...d, status: "Failed" } : d
            )
          );
        }

        if (log === "Done") {
          setDeployments((prev) =>
            prev.map((d) =>
              d.slug === slug ? { ...d, status: "Live" } : d
            )
          );
          ws.close();
        }
      } catch {
        setLines((prev) => [...prev, e.data]);
      }
    };

    ws.onerror = () => {
      setLines((prev) => [...prev, "WebSocket error"]);
    };

    ws.onclose = () => {
      setLines((prev) => [...prev, "Connection closed"]);
    };

    return () => {
      ws.close();
    };
  }, [channel, setDeployments]);

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

        <span className="terminal-label">
          {channel ?? "— no channel —"}
        </span>

        <button
          className="terminal-clear"
          onClick={() => setLines([])}
        >
          clear
        </button>
      </div>

      <div className="terminal-body" ref={bodyRef}>
        {lines.map((line, i) => (
          <div key={i} className="log-line">
            <span className="log-prefix">
              {String(i + 1).padStart(3, "0")}
            </span>
            <span className={`log-text log-${classifyLine(line)}`}>
              {line}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}