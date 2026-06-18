import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from '../pages/Dashboard'

vi.mock('../lib/supabase', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          order: vi.fn(() => ({
            data: [],
          })),
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
  it('renders header with user email', () => {
    render(
      <MemoryRouter>
        <Dashboard user={{ id: 'u1', email: 'test@test.com' }} profile={{ email: 'test@test.com' }} logout={vi.fn()} />
      </MemoryRouter>
    )
    expect(screen.getByText('test@test.com')).toBeInTheDocument()
  })

  it('renders new resume button', () => {
    render(
      <MemoryRouter>
        <Dashboard user={{ id: 'u1' }} profile={{}} logout={vi.fn()} />
      </MemoryRouter>
    )
    expect(screen.getByText('New Resume')).toBeInTheDocument()
  })

  it('shows admin badge when role is admin', () => {
    render(
      <MemoryRouter>
        <Dashboard user={{ id: 'u1' }} profile={{ role: 'admin' }} logout={vi.fn()} />
      </MemoryRouter>
    )
    expect(screen.getByText('Admin')).toBeInTheDocument()
  })
})
