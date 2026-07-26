import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useSupabaseAuth } from './hooks/useSupabaseAuth'
import Landing from './pages/Landing'
import Demo from './pages/Demo'
import AtsCheck from './pages/AtsCheck'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import ResumeEditor from './pages/ResumeEditor'
import PublicResume from './pages/PublicResume'
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
        {/* One persistent shell for all signed-in pages — a layout route
            keeps the sidebar mounted across navigation (no re-probe flicker) */}
        <Route
          element={
            <ProtectedRoute user={user} loading={loading}>
              <AppShell user={user} profile={profile} logout={logout}>
                <Outlet />
              </AppShell>
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard user={user} />} />
          <Route path="/resume/:resumeId" element={<ResumeEditor user={user} />} />
          {user && <Route path="/ats-check" element={<AtsCheck inShell />} />}
        </Route>
        <Route path="/demo" element={<Demo />} />
        <Route path="/r/:userId" element={<PublicResume />} />
        {!user && <Route path="/ats-check" element={<AtsCheck />} />}
        <Route
          path="/"
          element={user ? <Navigate to="/dashboard" replace /> : <Landing />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
