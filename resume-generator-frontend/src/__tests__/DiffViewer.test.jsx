import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import DiffViewer from '../components/DiffViewer'

describe('DiffViewer', () => {
  it('renders nothing when diff is null', () => {
    const { container } = render(<DiffViewer diff={null} onClose={() => {}} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders diff lines with correct coloring', () => {
    const diff = `--- v1
+++ v2
@@ -1,3 +1,3 @@
 line1
-old line
+new line
 line3`
    render(<DiffViewer diff={diff} onClose={() => {}} />)
    expect(screen.getByText('Version Diff')).toBeInTheDocument()
    expect(screen.getByText('-old line')).toBeInTheDocument()
    expect(screen.getByText('+new line')).toBeInTheDocument()
  })

  it('calls onClose when close button clicked', () => {
    const onClose = vi.fn()
    render(<DiffViewer diff="--- a\n+++ b" onClose={onClose} />)
    fireEvent.click(screen.getByText('Version Diff').closest('div').querySelector('button'))
    expect(onClose).toHaveBeenCalled()
  })
})
