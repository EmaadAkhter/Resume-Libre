import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import FresherWizard from '../components/FresherWizard'

describe('FresherWizard', () => {
  it('renders the profession picker first', () => {
    render(<FresherWizard onGenerate={vi.fn()} loading={false} />)
    expect(screen.getByText(/Software \/ IT/)).toBeInTheDocument()
  })

  it('advances to basic info after picking a profession', () => {
    render(<FresherWizard onGenerate={vi.fn()} loading={false} />)
    fireEvent.click(screen.getByText(/Software \/ IT/))
    expect(screen.getByText(/Full Name/)).toBeInTheDocument()
  })
})
