import React from "react";

export default function ResultCard({ result }) {
  if (!result) return null;
  return (
    <div className="result-card">
      <div className="result-row">
        <span className="result-label">Slug</span>
        <span className="result-value">{result.projectSlug}</span>
      </div>
      <div className="result-row">
        <span className="result-label">Live URL</span>
        <a
          href={result.url}
          target="_blank"
          rel="noreferrer"
          className="result-url"
        >
          {result.url}
        </a>
      </div>
    </div>
  );
}