import { describe, it, expect } from 'vitest'
import { useState } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import ProfileSources from '../components/ProfileSources'

function Harness({ initial = [] }) {
  const [sources, setSources] = useState(initial)
  return <ProfileSources sources={sources} onChange={setSources} />
}

const githubRow = { id: 'row-1', type: 'github', value: '' }

describe('ProfileSources', () => {
  it('renders a default github row', () => {
    render(<Harness initial={[githubRow]} />)
    expect(screen.getByText('GitHub')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('username')).toBeInTheDocument()
    expect(screen.getByLabelText('Remove GitHub profile')).toBeInTheDocument()
  })

  it('shows the empty-state hint when there are no rows', () => {
    render(<Harness initial={[]} />)
    expect(screen.getByText('Add GitHub, LinkedIn, ORCID or Hugging Face')).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  it('adds an ORCID row via the add-profile menu', () => {
    render(<Harness initial={[githubRow]} />)
    fireEvent.click(screen.getByRole('button', { name: /add profile/i }))
    fireEvent.click(screen.getByRole('button', { name: 'ORCID' }))
    expect(screen.getByPlaceholderText('0000-0002-1825-0097')).toBeInTheDocument()
    // menu closed after picking
    expect(screen.queryByRole('button', { name: 'Hugging Face' })).not.toBeInTheDocument()
  })

  it('allows adding the same type twice', () => {
    render(<Harness initial={[]} />)
    fireEvent.click(screen.getByRole('button', { name: /add profile/i }))
    fireEvent.click(screen.getByRole('button', { name: 'GitHub' }))
    fireEvent.click(screen.getByRole('button', { name: /add profile/i }))
    fireEvent.click(screen.getByRole('button', { name: 'GitHub' }))
    expect(screen.getAllByPlaceholderText('username')).toHaveLength(2)
    expect(screen.getAllByLabelText('Remove GitHub profile')).toHaveLength(2)
  })

  it('removes a row via its X button', () => {
    render(<Harness initial={[githubRow]} />)
    fireEvent.click(screen.getByLabelText('Remove GitHub profile'))
    expect(screen.queryByPlaceholderText('username')).not.toBeInTheDocument()
    expect(screen.getByText('Add GitHub, LinkedIn, ORCID or Hugging Face')).toBeInTheDocument()
  })

  it('shows one shared LinkedIn paste tip under linkedin rows', () => {
    render(
      <Harness
        initial={[
          { id: 'li-1', type: 'linkedin', value: '' },
          { id: 'li-2', type: 'linkedin', value: '' },
        ]}
      />
    )
    expect(screen.getAllByText(/pasting your LinkedIn text into Additional Information/i)).toHaveLength(1)
  })
})
