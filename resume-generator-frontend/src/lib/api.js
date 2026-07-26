import { supabase } from './supabase'

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function authHeaders() {
  const { data: { session } } = await supabase.auth.getSession()
  return session ? { Authorization: `Bearer ${session.access_token}` } : {}
}

// fetch wrapper that attaches the Supabase JWT to backend API calls
export async function apiFetch(path, options = {}) {
  const headers = { ...(await authHeaders()), ...(options.headers || {}) }
  return fetch(`${API_URL}${path}`, { ...options, headers })
}
