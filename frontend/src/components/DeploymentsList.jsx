import React from "react";

export default function DeploymentsList({ items = [] }) {
  if (!items.length) return <div className="empty">No deployments yet.</div>;
  return (
    <div className="deployments-list">
      {items
        .slice()
        .reverse()
        .map((d, i) => (
          <div key={i} className="deployment-item">
            <div>
              <div className="dep-slug">{d.slug}</div>
              <div className="dep-time">{d.time}</div>
            </div>
            <a href={d.url} target="_blank" rel="noreferrer">
              {d.url}
            </a>
          </div>
        ))}
    </div>
  );
}
