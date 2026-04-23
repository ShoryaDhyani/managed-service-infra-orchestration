import React, { useState } from 'react'
import { signup } from '../auth'

export default function SignupForm({ onSuccess, onCancel }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError(null)
    if (password !== confirm) { setError('Passwords do not match'); return }
    setLoading(true)
    try {
      await signup(username.trim(), password)
      setUsername('')
      setPassword('')
      setConfirm('')
      onSuccess && onSuccess()
    } catch (err) {
      setError(err.message || 'Signup failed')
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
      <div className="form-group">
        <label>Confirm Password</label>
        <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} />
      </div>
      {error && <div className="auth-error">{error}</div>}
      <div style={{display:'flex', gap:8}}>
        <button className="btn" type="submit" disabled={loading}>{loading ? 'Creating...' : 'Create account'}</button>
        <button type="button" className="btn" onClick={onCancel}>cancel</button>
      </div>
    </form>
  )
}
