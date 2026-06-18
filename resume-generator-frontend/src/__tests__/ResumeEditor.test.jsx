import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ResumeEditor from '../pages/ResumeEditor'

vi.mock('../lib/supabase', () => ({
  supabase: {
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          single: vi.fn(() => ({ data: null })),
        })),
      })),
    })),
  },
}))

vi.mock('../hooks/useGenerationStream', () => ({
  useGenerationStream: () => ({ streamGeneration: vi.fn() }),
}))

vi.mock('../hooks/useTemplates', () => ({
  useTemplates: () => ({
    templates: [],
    selectedTemplate: null,
    selectTemplate: vi.fn(),
    uploadTemplate: vi.fn(),
  }),
}))

describe('ResumeEditor', () => {
  it('renders loading state initially', () => {
    render(
      <MemoryRouter>
        <ResumeEditor user={{ id: 'u1' }} />
      </MemoryRouter>
    )
    expect(screen.getByText('Loading resume...')).toBeInTheDocument()
  })
})
