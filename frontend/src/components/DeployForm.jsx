import React, { useState } from "react";
import { deployProject } from "../api";

export default function DeployForm({ onDeployed }) {
  const [gitURL, setGitURL] = useState("");
  const [slug, setSlug] = useState("");
  const [loading, setLoading] = useState(false);
  const [type, setType] = useState("none");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!gitURL) {
      alert("Please enter a Git repository URL.");
      return;
    }
    if (type === "none") {
      alert("Please select a project type.");
      return;
    }
    setLoading(true);
    try {
      const json = await deployProject({
        gitURL,
        slug: slug || undefined,
        type,
      });
      const data = json?.data || json;
      if (data) {
        onDeployed(data);
      } else {
        alert("Unexpected response from server.");
      }
    } catch (err) {
      console.error(err);
      alert(err.message || "Deployment failed. Check the console for details.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="deploy-form" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="dep-type">Project type</label>
        <select
          id="dep-type"
          value={type}
          onChange={(e) => setType(e.target.value)}
        >
          <option value="none" disabled>
            Select a type
          </option>
          <option value="node">Node.js</option>
          <option value="static">Static (HTML / CSS)</option>
        </select>
      </div>

      <div className="field">
        <label htmlFor="dep-url">Git repository URL</label>
        <input
          id="dep-url"
          type="text"
          value={gitURL}
          onChange={(e) => setGitURL(e.target.value)}
          placeholder="https://github.com/user/repo"
        />
      </div>

      <div className="field">
        <label htmlFor="dep-slug">
          Slug <span className="label-hint">(optional)</span>
        </label>
        <input
          id="dep-slug"
          type="text"
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
          placeholder="my-app"
        />
      </div>

      <button type="submit" className="deploy-btn" disabled={loading}>
        {loading ? (
          <>
            <span className="spinner" aria-hidden="true" />
            Deploying…
          </>
        ) : (
          "Deploy →"
        )}
      </button>
    </form>
  );
}