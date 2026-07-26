import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from '../pages/Dashboard'
import AppShell from '../components/AppShell'

vi.mock('../lib/supabase', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          order: vi.fn(() => ({
            data: [],
          })),
          // AppShell's published-state probe
          maybeSingle: vi.fn(() => Promise.resolve({ data: null })),
        })),
      })),
      insert: vi.fn(() => ({ select: vi.fn(() => ({ single: vi.fn(() => ({ data: {} })) })) })),
    })),
  },
}))

vi.mock('react-router-dom', async () => ({
  ...(await vi.importActual('react-router-dom')),
  useNavigate: () => vi.fn(),
}))

describe('Dashboard', () => {
  it('renders shell sidebar with user email', () => {
    render(
      <MemoryRouter>
        <AppShell user={{ id: 'u1', email: 'test@test.com' }} profile={{ email: 'test@test.com' }} logout={vi.fn()}>
          <Dashboard user={{ id: 'u1', email: 'test@test.com' }} />
        </AppShell>
      </MemoryRouter>
    )
    expect(screen.getByText('test@test.com')).toBeInTheDocument()
  })

  it('renders new resume button', () => {
    render(
      <MemoryRouter>
        <Dashboard user={{ id: 'u1' }} />
      </MemoryRouter>
    )
    expect(screen.getByText('New Resume')).toBeInTheDocument()
  })

  it('shows admin badge when role is admin', () => {
    render(
      <MemoryRouter>
        <AppShell user={{ id: 'u1' }} profile={{ role: 'admin' }} logout={vi.fn()}>
          <Dashboard user={{ id: 'u1' }} />
        </AppShell>
      </MemoryRouter>
    )
    expect(screen.getByText('Admin')).toBeInTheDocument()
  })
})
