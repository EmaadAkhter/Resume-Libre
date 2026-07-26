import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import AtsReport from '../components/ats/AtsReport'

const report = {
  filename: 'resume.pdf',
  summary: { passed: 2, warned: 1, failed: 0 },
  checks: [
    {
      id: 'contact-info',
      status: 'pass',
      reason: 'Both found.',
      fix: 'No action needed.',
      category: 'contact',
    },
    {
      id: 'bullet-density',
      status: 'warn',
      reason: 'Only 5% of lines are bullet points.',
      fix: 'Convert experience into bullet points.',
      category: 'content',
    },
    {
      id: 'file-size',
      status: 'pass',
      reason: '0.1 MB.',
      fix: 'No action needed.',
      category: 'file',
    },
  ],
}

describe('AtsReport grouping', () => {
  it('renders one header per category with check counts', () => {
    render(<AtsReport report={report} />)
    expect(screen.getByText('Contact & Links')).toBeInTheDocument()
    expect(screen.getByText('Content & Writing')).toBeInTheDocument()
    expect(screen.getByText('File')).toBeInTheDocument()
    expect(screen.getAllByText('1 check')).toHaveLength(3)
  })

  it('sorts categories with warnings ahead of all-pass ones', () => {
    render(<AtsReport report={report} />)
    const headers = screen
      .getAllByText(/^(Contact & Links|Content & Writing|File)$/)
      .map((el) => el.textContent)
    expect(headers[0]).toBe('Content & Writing')
  })

  it('shows friendly titles for v2 check ids', () => {
    render(<AtsReport report={report} />)
    expect(screen.getByText('Bullet density')).toBeInTheDocument()
    expect(screen.getByText('File size')).toBeInTheDocument()
  })

  it('keeps the compact mode a flat non-pass list', () => {
    render(<AtsReport report={report} compact />)
    expect(screen.queryByText('Content & Writing')).not.toBeInTheDocument()
    expect(screen.getByText('Bullet density')).toBeInTheDocument()
    expect(screen.queryByText('File size')).not.toBeInTheDocument()
  })
})
