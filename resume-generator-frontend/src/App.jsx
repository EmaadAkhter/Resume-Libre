import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useSupabaseAuth } from './hooks/useSupabaseAuth'
import Landing from './pages/Landing'
import Demo from './pages/Demo'
import AtsCheck from './pages/AtsCheck'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import ResumeEditor from './pages/ResumeEditor'
import AppShell from './components/AppShell'
import LoadingScreen from './components/LoadingScreen'
import ToastContainer from './components/ToastContainer'
import BackendStatusBanner from './components/BackendStatusBanner'

function ProtectedRoute({ children, user, loading }) {
  if (loading) {
    return <LoadingScreen />
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return children
}

export default function App() {
  const { user, profile, loading, login, register, logout } = useSupabaseAuth()

  return (
    <BrowserRouter>
      <ToastContainer />
      <BackendStatusBanner />

      <Routes>
        <Route
          path="/login"
          element={user ? <Navigate to="/dashboard" replace /> : <Login login={login} />}
        />
        <Route
          path="/register"
          element={user ? <Navigate to="/dashboard" replace /> : <Register register={register} />}
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute user={user} loading={loading}>
              <AppShell user={user} profile={profile} logout={logout}>
                <Dashboard user={user} />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/resume/:resumeId"
          element={
            <ProtectedRoute user={user} loading={loading}>
              <AppShell user={user} profile={profile} logout={logout}>
                <ResumeEditor user={user} />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route path="/demo" element={<Demo />} />
        <Route
          path="/ats-check"
          element={
            user ? (
              <AppShell user={user} profile={profile} logout={logout}>
                <AtsCheck inShell />
              </AppShell>
            ) : (
              <AtsCheck />
            )
          }
        />
        <Route
          path="/"
          element={user ? <Navigate to="/dashboard" replace /> : <Landing />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
