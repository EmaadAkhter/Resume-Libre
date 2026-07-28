import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'

const PASSING = {
  summary: { passed: 30, warned: 1, failed: 0 },
  extracted: {
    name: { value: 'Jane Doe', confidence: 'high' },
    email: { value: 'jane@example.com', confidence: 'high' },
    skills: { value: ['Python', 'Docker', 'React'], confidence: 'high' },
  },
}

async function renderWith(env, report) {
  vi.resetModules()
  vi.stubEnv('VITE_JOB_SEARCH_URL', env)
  const { default: JobMatchCta } = await import('../components/ats/JobMatchCta')
  return render(<JobMatchCta report={report} />)
}

describe('JobMatchCta', () => {
  beforeEach(() => vi.resetModules())
  afterEach(() => vi.unstubAllEnvs())

  it('renders nothing when no partner URL is configured', async () => {
    const { container } = await renderWith('', PASSING)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders a tracked link on the pass path', async () => {
    await renderWith('https://jobs.example.com/search?q={query}&aid=X1', PASSING)
    const link = screen.getByRole('link', { name: /browse matching roles/i })
    expect(link).toHaveAttribute('href', 'https://jobs.example.com/search?q=Python%20Docker%20React&aid=X1')
    expect(link).toHaveAttribute('rel', expect.stringContaining('sponsored'))
  })

  // The gate that keeps the incentive honest: no revenue from a failing
  // resume, so the checker can never profit by inventing problems.
  it('stays hidden when any check failed', async () => {
    const failing = { ...PASSING, summary: { passed: 20, warned: 3, failed: 2 } }
    const { container } = await renderWith('https://jobs.example.com/?q={query}', failing)
    expect(container).toBeEmptyDOMElement()
  })

  it('never puts personal data in the outbound URL', async () => {
    await renderWith('https://jobs.example.com/?q={query}', PASSING)
    const href = screen.getByRole('link', { name: /browse matching roles/i }).getAttribute('href')
    expect(href).not.toContain('Jane')
    expect(href).not.toContain('jane%40example.com')
  })

  it('renders nothing when no skills were extracted', async () => {
    const noSkills = { ...PASSING, extracted: { skills: { value: [] } } }
    const { container } = await renderWith('https://jobs.example.com/?q={query}', noSkills)
    expect(container).toBeEmptyDOMElement()
  })
})
