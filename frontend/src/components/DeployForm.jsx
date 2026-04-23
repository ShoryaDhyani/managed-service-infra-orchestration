import React, { useState } from 'react'
import { createProject } from '../api'

export default function DeployForm({ onDeployed }) {
  const [gitURL, setGitURL] = useState('')
  const [slug, setSlug] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    if (!gitURL) { alert('Please enter a Git repository URL'); return }
    setLoading(true)
    try {
      const json = await createProject({ gitURL, slug: slug || undefined })
      if (json && json.data) {
        onDeployed(json.data)
      } else {
        alert('Unexpected response from server')
      }
    } catch (err) {
      console.error(err)
      alert('Deployment failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="deploy-form" onSubmit={submit}>
      <div className="form-group">
        <label>Git Repository URL</label>
        <input value={gitURL} onChange={e => setGitURL(e.target.value)} placeholder="https://github.com/user/repo" />
      </div>
      <div className="form-group">
        <label>Project Slug (optional)</label>
        <input value={slug} onChange={e => setSlug(e.target.value)} placeholder="auto-generated" />
      </div>
      <button id="deploy-btn" type="submit" className="btn primary" disabled={loading}>{loading ? 'Deploying...' : 'Deploy Now'}</button>
    </form>
  )
}
