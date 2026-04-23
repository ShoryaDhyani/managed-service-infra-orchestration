import React from "react";

export default function ResultCard({ result }) {
  if (!result) return null;
  return (
    <div className="result-card">
      <div>
        Project Slug: <strong>{result.projectSlug}</strong>
      </div>
      <div>
        Live URL:{" "}
        <a href={result.url} target="_blank" rel="noreferrer">
          {result.url}
        </a>
      </div>
    </div>
  );
}
