import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TemplatePicker from '../components/TemplatePicker'

const templates = [
  { id: 't1', name: 'Classic MD', format: 'md', is_admin_only: false },
  { id: 't2', name: 'LaTeX Pro', format: 'tex', is_admin_only: true },
]

describe('TemplatePicker', () => {
  it('renders select with all templates', () => {
    render(
      <TemplatePicker templates={templates} selected={null} onSelect={() => {}} user={{ id: 'u1' }} />
    )
    const select = screen.getByRole('combobox')
    expect(select).toBeInTheDocument()
    expect(screen.getByText('Classic MD (MD)')).toBeInTheDocument()
    expect(screen.getByText('[Admin] LaTeX Pro (TEX)')).toBeInTheDocument()
  })

  it('shows no-template option by default', () => {
    render(
      <TemplatePicker templates={[]} selected={null} onSelect={() => {}} user={{ id: 'u1' }} />
    )
    expect(screen.getByText('No template (AI decides format)')).toBeInTheDocument()
  })

  it('calls onSelect when template selected', () => {
    const onSelect = vi.fn()
    render(
      <TemplatePicker templates={templates} selected={null} onSelect={onSelect} user={{ id: 'u1' }} />
    )
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 't1' } })
    expect(onSelect).toHaveBeenCalledWith(templates[0])
  })
})
