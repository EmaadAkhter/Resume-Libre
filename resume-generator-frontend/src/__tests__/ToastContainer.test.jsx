import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ToastContainer from '../components/ToastContainer'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'

describe('ToastContainer', () => {
  it('renders empty initially', () => {
    const { container } = render(<ToastContainer />)
    expect(container.querySelector('.fixed')).toBeInTheDocument()
  })

  it('shows toast on notification:show event', async () => {
    render(<ToastContainer />)
    eventBus.emit(EVENTS.NOTIFICATION_SHOW, { type: 'success', message: 'Test toast!' })
    await waitFor(() => {
      expect(screen.getByText('Test toast!')).toBeInTheDocument()
    })
  })

  it('shows error toast with correct styling', async () => {
    render(<ToastContainer />)
    eventBus.emit(EVENTS.NOTIFICATION_SHOW, { type: 'error', message: 'Error occurred!' })
    await waitFor(() => {
      const toast = screen.getByText('Error occurred!')
      expect(toast.closest('div').className).toContain('red')
    })
  })

  it('auto-dismisses after duration', async () => {
    render(<ToastContainer />)
    eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
      type: 'info',
      message: 'Temp toast',
      duration: 100,
    })
    await waitFor(() => {
      expect(screen.getByText('Temp toast')).toBeInTheDocument()
    })
    await waitFor(
      () => {
        expect(screen.queryByText('Temp toast')).not.toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })
})
