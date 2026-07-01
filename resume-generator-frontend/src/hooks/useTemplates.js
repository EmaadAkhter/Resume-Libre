import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'

export function useTemplates(user) {
  const [templates, setTemplates] = useState([])
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchTemplates = useCallback(async () => {
    if (!user) return
    setLoading(true)
    try {
      const { data, error } = await supabase.from('templates').select('*').order('created_at')
      if (error) throw error
      setTemplates(data || [])
    } catch (err) {
      console.error('Failed to fetch templates:', err)
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    fetchTemplates()
  }, [fetchTemplates])

  const selectTemplate = useCallback((template) => {
    setSelectedTemplate(template)
    eventBus.emit(EVENTS.TEMPLATE_SELECTED, template)
  }, [])

  const uploadTemplate = useCallback(
    async (name, content, format, description = '', isPublic = false) => {
      if (!user) return
      const isAdmin = user?.role === 'admin'
      const { data, error } = await supabase
        .from('templates')
        .insert({
          name,
          content,
          format,
          description,
          is_public: isAdmin ? isPublic : false,
          is_admin_only: false,
          created_by: user.id,
        })
        .select()
        .single()

      if (error) throw error
      setTemplates((prev) => [...prev, data])
      eventBus.emit(EVENTS.TEMPLATE_UPLOADED, data)
      return data
    },
    [user]
  )

  return {
    templates,
    selectedTemplate,
    loading,
    fetchTemplates,
    selectTemplate,
    uploadTemplate,
  }
}
