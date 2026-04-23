import React, { useState } from 'react'
import { login } from '../auth'

export default function LoginForm({ onSuccess, onCancel }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(username.trim(), password)
      setUsername('')
      setPassword('')
      onSuccess && onSuccess()
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <div className="form-group">
        <label>Username</label>
        <input value={username} onChange={e => setUsername(e.target.value)} />
      </div>
      <div className="form-group">
        <label>Password</label>
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
      </div>
      {error && <div className="auth-error">{error}</div>}
      <div style={{display:'flex', gap:8}}>
        <button className="btn" type="submit" disabled={loading}>{loading ? 'Signing in...' : 'Sign in'}</button>
        <button type="button" className="btn" onClick={onCancel}>cancel</button>
      </div>
    </form>
  )
}
