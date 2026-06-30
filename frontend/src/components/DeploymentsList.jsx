import React from "react";

export default function DeploymentsList({
  items = [],
}) {
  if (!items.length) {
    return (
      <div className="history-empty">
        No deployments yet.
      </div>
    );
  }

  return (
    <div className="dep-list">
      {[...items].reverse().map((d, i) => (
        <div className="dep-item" key={i}>
          <div>
            <div className="dep-slug">
              {d.slug}
            </div>

            <div className="dep-time">
              {d.time}
            </div>
          </div>

          <div className="dep-item-right">
            <a
              href={d.url}
              target="_blank"
              rel="noreferrer"
              className="dep-url"
            >
              {d.url}
            </a>
            {console.log(d)}
            <span className={`dep-badge dep-badge--${(d.status || "Building").toLowerCase()}`}>
              {d.status}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}