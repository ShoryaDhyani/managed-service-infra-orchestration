import React, { useEffect, useState } from 'react'
import { API_BASE } from '../api'
import { getCurrentUser, logout } from '../auth'
import LoginForm from './LoginForm'
import SignupForm from './SignupForm'

export default function AuthButton() {
  const [user, setUser] = useState(() => getCurrentUser())
  const [showLogin, setShowLogin] = useState(false)
  const [showSignup, setShowSignup] = useState(false)

  useEffect(() => {
    setUser(getCurrentUser())
  }, [])

  async function githubLogin() {
    try {
      const res = await fetch(`${API_BASE}/auth/github/login`)
      if (!res.ok) throw new Error('Auth request failed')
      const data = await res.json()
      if (data.auth_url) {
        window.location.href = data.auth_url
      } else {
        alert('No auth URL returned')
      }
    } catch (e) {
      console.error(e)
      alert('Failed to start GitHub login')
    }
  }

  function handleLogout() {
    logout()
    setUser(null)
  }

  function onAuthSuccess() {
    setShowLogin(false)
    setShowSignup(false)
    setUser(getCurrentUser())
  }

  if (user) {
    return (
      <div style={{display:'flex', alignItems:'center', gap:8}}>
        <div>Hi, <strong>{user.username}</strong></div>
        <button className="btn" onClick={handleLogout}>Logout</button>
        <button className="btn" onClick={githubLogin}>Sign in with GitHub</button>
      </div>
    )
  }

  return (
    <div style={{display:'flex', alignItems:'center', gap:8}}>
      <button className="btn" onClick={() => setShowLogin(v => !v)}>Login</button>
      <button className="btn" onClick={() => setShowSignup(v => !v)}>Signup</button>
      <button className="btn" onClick={githubLogin}>Sign in with GitHub</button>

      <div style={{minWidth:280}}>
        {showLogin && <LoginForm onSuccess={onAuthSuccess} onCancel={() => setShowLogin(false)} />}
        {showSignup && <SignupForm onSuccess={onAuthSuccess} onCancel={() => setShowSignup(false)} />}
      </div>
    </div>
  )
}
