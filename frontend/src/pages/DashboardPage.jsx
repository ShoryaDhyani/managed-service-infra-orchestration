import React, { useState, useEffect, useCallback } from "react";
import Sidebar from "../components/Sidebar";
import DeployForm from "../components/DeployForm";
import ResultCard from "../components/ResultCard";
import LogsPanel from "../components/LogsPanel";

import { useAuth } from "../context/AuthContext";
import { getProjects } from "../api";

export default function DashboardPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");

  // Projects from API
  const [projects, setProjects] = useState([]);
  const [projectsLoading, setProjectsLoading] = useState(true);

  // Deploy state
  const [result, setResult] = useState(null);
  const [logsChannel, setLogsChannel] = useState(null);

  // Fetch projects
  const fetchProjects = useCallback(async () => {
    setProjectsLoading(true);
    try {
      const data = await getProjects();
      setProjects(data.data || data || []);
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    } finally {
      setProjectsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  function handleDeployed(data) {
    setResult(data);
    const slug = data.projectSlug || data.slug;
    setLogsChannel(`logs:${slug}`);
    setActiveTab("deploy");
    setTimeout(fetchProjects, 2000);
  }

  // Compute stats
  const liveCount = Array.isArray(projects)
    ? projects.filter((p) => (p.status || "").toLowerCase() === "live" || (p.status || "").toLowerCase() === "running").length
    : 0;
  const buildingCount = Array.isArray(projects)
    ? projects.filter((p) => (p.status || "").toLowerCase() === "building" || (p.status || "").toLowerCase() === "pending").length
    : 0;
  const failedCount = Array.isArray(projects)
    ? projects.filter((p) => (p.status || "").toLowerCase() === "failed").length
    : 0;
  const totalProjects = Array.isArray(projects) ? projects.length : 0;

  const tabTitles = {
    overview: "Overview",
    projects: "Projects",
    deploy: "Deploy",
  };

  return (
    <div className="dashboard-layout">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <div className="main-content">
        {/* Top bar */}
        <header className="topbar">
          <div className="topbar-left">
            <h1 className="topbar-title">{tabTitles[activeTab] || "Dashboard"}</h1>
            <span className="topbar-breadcrumb">/ {user?.username || "user"}</span>
          </div>
          <div className="topbar-right">
            <span className="topbar-stat">
              <span className="topbar-dot" />
              {totalProjects} project{totalProjects !== 1 ? "s" : ""}
            </span>
          </div>
        </header>

        {/* Page content */}
        <div className="page-content" key={activeTab}>
          {activeTab === "overview" && (
            <OverviewTab
              totalProjects={totalProjects}
              liveCount={liveCount}
              buildingCount={buildingCount}
              failedCount={failedCount}
              projects={projects}
              projectsLoading={projectsLoading}
              onDeployed={handleDeployed}
            />
          )}
          {activeTab === "projects" && (
            <ProjectsTab
              projects={projects}
              loading={projectsLoading}
              onRefresh={fetchProjects}
            />
          )}
          {activeTab === "deploy" && (
            <DeployTab
              result={result}
              logsChannel={logsChannel}
              onDeployed={handleDeployed}
            />
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── Overview Tab ──────────────────────────────────────── */
function OverviewTab({ totalProjects, liveCount, buildingCount, failedCount, projects, projectsLoading, onDeployed }) {
  return (
    <>
      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-label">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></svg>
            Total Projects
          </div>
          <div className="stat-value accent">{totalProjects}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
            Live
          </div>
          <div className="stat-value green">{liveCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" /><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" /></svg>
            Building
          </div>
          <div className="stat-value amber">{buildingCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" /></svg>
            Failed
          </div>
          <div className="stat-value red">{failedCount}</div>
        </div>
      </div>

      {/* Quick actions + Recent */}
      <div className="dashboard-grid">
        <div>
          {/* Quick deploy card */}
          <div className="section-card" style={{ marginBottom: 24 }}>
            <div className="section-card-header">
              <div className="section-card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="16 16 12 12 8 16" />
                  <line x1="12" y1="12" x2="12" y2="21" />
                  <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
                </svg>
                Quick Deploy
              </div>
            </div>
            <div className="section-card-body">
              <DeployForm onDeployed={onDeployed} />
            </div>
          </div>
        </div>

        {/* Right column — projects */}
        <div>
          <div className="section-card">
            <div className="section-card-header">
              <div className="section-card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                </svg>
                Your Projects
              </div>
              <span className="section-card-badge">{totalProjects}</span>
            </div>
            <div style={{ padding: 0 }}>
              {projectsLoading ? (
                <div style={{ padding: 20 }}>
                  <div className="skeleton skeleton-line" />
                  <div className="skeleton skeleton-line" />
                  <div className="skeleton skeleton-line" />
                </div>
              ) : (
                <ProjectsListView projects={projects} />
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

/* ─── Projects Tab ──────────────────────────────────────── */
function ProjectsTab({ projects, loading, onRefresh }) {
  return (
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
          </svg>
          All Projects
        </div>
        <button
          className="section-card-badge"
          style={{ cursor: "pointer", border: "none", background: "var(--accent-bg)", color: "var(--accent-light)" }}
          onClick={onRefresh}
        >
          ↻ Refresh
        </button>
      </div>
      <div style={{ padding: 0 }}>
        {loading ? (
          <div style={{ padding: 20 }}>
            <div className="skeleton skeleton-line" />
            <div className="skeleton skeleton-line" />
            <div className="skeleton skeleton-line" />
            <div className="skeleton skeleton-line" />
          </div>
        ) : (
          <ProjectsListView projects={projects} />
        )}
      </div>
    </div>
  );
}

/* ─── Deploy Tab ───────────────────────────────────────── */
function DeployTab({ result, logsChannel, onDeployed }) {

  return (
    <div className="dashboard-grid">
      <div>
        <div className="section-card">
          <div className="section-card-header">
            <div className="section-card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="16 16 12 12 8 16" />
                <line x1="12" y1="12" x2="12" y2="21" />
                <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
              </svg>
              New Deployment
            </div>
          </div>
          <div className="section-card-body">
            <DeployForm onDeployed={onDeployed} />
            {result && <ResultCard result={result} />}
          </div>
        </div>


      </div>

      {/* Logs terminal */}
      <div>
        <LogsPanel channel={logsChannel} />
      </div>
    </div>
  );
}

/* ─── Shared Projects List View ─────────────────────────── */
function ProjectsListView({ projects }) {
  if (!Array.isArray(projects) || projects.length === 0) {
    return (
      <div className="projects-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
        </svg>
        <p>No projects yet. Deploy your first project to get started.</p>
      </div>
    );
  }

  return (
    <div className="projects-table">
      <div className="projects-header">
        <span>Name</span>
        <span>URL</span>
        <span>Type</span>
        <span>Status</span>
      </div>
      {projects.map((p, i) => {
        const status = (p.status || "pending").toLowerCase();
        const slug = p.slug || p.projectSlug || p.name || `project-${i}`;
        const url = p.url || p.liveUrl || p.project_url || "";
        const type = p.type || "—";

        return (
          <div className="project-row" key={i}>
            <div className="project-name">
              <span className={`project-name-dot ${status}`} />
              {slug}
            </div>
            <div className="project-url">
              {url ? (
                <a href={url} target="_blank" rel="noreferrer">{url}</a>
              ) : (
                <span style={{ opacity: 0.4 }}>—</span>
              )}
            </div>
            <span className="project-type-badge">{type}</span>
            <span className={`project-status-badge ${status}`}>{status}</span>
          </div>
        );
      })}
    </div>
  );
}
