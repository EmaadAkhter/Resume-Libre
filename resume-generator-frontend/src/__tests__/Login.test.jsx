import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Login from '../pages/Login'

const mockLogin = vi.fn()
const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => ({
  ...(await vi.importActual('react-router-dom')),
  useNavigate: () => mockNavigate,
}))

describe('Login', () => {
  it('renders email and password fields', () => {
    render(
      <MemoryRouter>
        <Login login={mockLogin} />
      </MemoryRouter>
    )
    expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument()
  })

  it('renders sign in button', () => {
    render(
      <MemoryRouter>
        <Login login={mockLogin} />
      </MemoryRouter>
    )
    expect(screen.getByText('Sign In')).toBeInTheDocument()
  })

  it('calls login on form submit', () => {
    render(
      <MemoryRouter>
        <Login login={mockLogin} />
      </MemoryRouter>
    )
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
      target: { value: 'test@test.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'password' },
    })
    fireEvent.click(screen.getByText('Sign In'))
    expect(mockLogin).toHaveBeenCalledWith('test@test.com', 'password')
  })
})
