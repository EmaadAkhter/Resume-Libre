import { useCallback } from 'react'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'

export function useGenerationStream() {
  const streamGeneration = useCallback(async (params, onToken, onDone, onError) => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const queryParams = new URLSearchParams()

    if (params.github_username) queryParams.set('github_username', params.github_username)
    if (params.additional_info) queryParams.set('additional_info', params.additional_info)
    if (params.priority) queryParams.set('priority', params.priority)
    if (params.custom_system_prompt) queryParams.set('custom_system_prompt', params.custom_system_prompt)
    if (params.resume_template) queryParams.set('resume_template', params.resume_template)
    if (params.template_format) queryParams.set('template_format', params.template_format)

    eventBus.emit(EVENTS.GENERATION_STARTED)

    try {
      const response = await fetch(`${apiUrl}/generate-resume-stream?${queryParams}`, {
        method: 'GET',
        headers: { Accept: 'text/event-stream' },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to start generation stream')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.event === 'token') {
                fullContent += data.content
                eventBus.emit(EVENTS.GENERATION_TOKEN, data.content)
                onToken?.(data.content, fullContent)
              } else if (data.event === 'done') {
                eventBus.emit(EVENTS.GENERATION_COMPLETED, data.content)
                onDone?.(data.content || fullContent)
                return data.content || fullContent
              } else if (data.event === 'error') {
                throw new Error(data.content)
              }
            } catch (e) {
              if (e.message && !e.message.includes('JSON')) {
                eventBus.emit(EVENTS.GENERATION_FAILED, e.message)
                onError?.(e.message)
                throw e
              }
            }
          }
        }
      }

      eventBus.emit(EVENTS.GENERATION_COMPLETED, fullContent)
      onDone?.(fullContent)
      return fullContent
    } catch (err) {
      eventBus.emit(EVENTS.GENERATION_FAILED, err.message)
      onError?.(err.message)
      throw err
    }
  }, [])

  return { streamGeneration }
}
