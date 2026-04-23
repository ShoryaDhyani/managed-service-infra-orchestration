// Simple client-side auth (for demo only). Uses Web Crypto to hash passwords
// Stores users in localStorage under 'ms_users' and session in 'ms_session'.

function getUsers() {
  try {
    return JSON.parse(localStorage.getItem('ms_users') || '{}')
  } catch {
    return {}
  }
}

function saveUsers(users) {
  localStorage.setItem('ms_users', JSON.stringify(users))
}

async function hashPassword(password) {
  const enc = new TextEncoder()
  const data = enc.encode(password)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

export async function signup(username, password) {
  if (!username || !password) throw new Error('username and password required')
  const users = getUsers()
  if (users[username]) throw new Error('User already exists')
  const hashed = await hashPassword(password)
  users[username] = { passwordHash: hashed, createdAt: Date.now() }
  saveUsers(users)
  localStorage.setItem('ms_session', username)
  return { username }
}

export async function login(username, password) {
  if (!username || !password) throw new Error('username and password required')
  const users = getUsers()
  const user = users[username]
  if (!user) throw new Error('Unknown user')
  const hashed = await hashPassword(password)
  if (hashed !== user.passwordHash) throw new Error('Invalid credentials')
  localStorage.setItem('ms_session', username)
  return { username }
}

export function logout() {
  localStorage.removeItem('ms_session')
}

export function getCurrentUser() {
  const username = localStorage.getItem('ms_session')
  if (!username) return null
  const users = getUsers()
  if (!users[username]) return null
  return { username }
}
