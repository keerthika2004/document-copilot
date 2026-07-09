import { useState, useEffect, useRef } from 'react'
import { env } from '@/lib/env'
import { supabase } from '@/lib/supabase'
import { api, type Message } from '@/lib/api'

interface UseChatOptions {
  threadId: string
  initialMessages?: Message[]
}

export function useChat({ threadId, initialMessages = [] }: UseChatOptions) {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const abortControllerRef = useRef<AbortController | null>(null)

  // Sync messages when initialMessages updates (e.g. when changing threads)
  useEffect(() => {
    setMessages(initialMessages)
    setError(null)
    setLoading(false)

    // Abort any active streams when switching threads
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
  }, [threadId, initialMessages])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  const sendMessage = async (contentToSend?: string) => {
    const text = contentToSend || input
    if (!text.trim() || loading) return

    setInput('')
    setError(null)
    setLoading(true)

    // 1. Construct user message and temporarily append it
    const userMsg: Message = {
      id: crypto.randomUUID(),
      thread_id: threadId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }

    const updatedMessages = [...messages, userMsg]
    setMessages(updatedMessages)

    // Create an assistant placeholder message
    const assistantMsgId = crypto.randomUUID()
    const assistantPlaceholder: Message = {
      id: assistantMsgId,
      thread_id: threadId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
    }

    setMessages([...updatedMessages, assistantPlaceholder])

    // Create AbortController for cancelable streams
    const controller = new AbortController()
    abortControllerRef.current = controller

    try {
      // 2. Fetch JWT token from Supabase Auth
      const {
        data: { session },
      } = await supabase.auth.getSession()
      const token = session?.access_token

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      // 3. Initiate post stream request
      const url = `${env.apiBaseUrl.replace(/\/$/, '')}/chat/stream`
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          threadId,
          messages: updatedMessages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
        signal: controller.signal,
      })

      if (!response.ok) {
        let errText = 'Failed to generate response'
        try {
          const errJson = await response.json()
          errText = errJson?.detail || errText
        } catch {
          // Fall back if response is not JSON
        }
        throw new Error(errText)
      }

      // 4. Stream response body chunks
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) {
        throw new Error('Response stream reader not available.')
      }

      let assistantContent = ''
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) {
          // Re-fetch thread messages to ensure fully persisted citations, metadata, and final IDs are displayed
          try {
            const refreshed = await api.messages.list(threadId)
            if (Array.isArray(refreshed)) {
              setMessages(refreshed)
            }
          } catch (refreshErr) {
            console.warn('Failed to refresh messages on stream done:', refreshErr)
          }
          window.dispatchEvent(new Event('chat:refresh-threads'))
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')

        // Leave the last partial line in the buffer
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue

          // Vercel AI SDK Data Stream Protocol parsing:
          // 0: -> Text delta
          // 2: -> Data / annotations (citations, confidence_summary)
          // e: -> Error message
          if (line.startsWith('0:')) {
            try {
              const textDelta = JSON.parse(line.substring(2))
              assistantContent += textDelta

              // Update assistant message with accumulated content
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId ? { ...m, content: assistantContent } : m
                )
              )
            } catch (jsonErr) {
              console.warn('Failed to parse text delta chunk:', line, jsonErr)
            }
          } else if (line.startsWith('2:')) {
            try {
              const dataArray = JSON.parse(line.substring(2))
              if (Array.isArray(dataArray) && dataArray.length > 0) {
                const meta = dataArray[0]
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, metadata_json: meta, citations: meta.citations }
                      : m
                  )
                )
              }
            } catch (jsonErr) {
              console.warn('Failed to parse data annotation chunk:', line, jsonErr)
            }
          } else if (line.startsWith('e:')) {
            try {
              const errorMsg = JSON.parse(line.substring(2))
              throw new Error(errorMsg)
            } catch (jsonErr) {
              throw new Error('An error occurred during chat stream generation.')
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('Stream aborted.')
        return
      }

      const errMsg = err?.message || 'Connection failed. Please check your network.'
      setError(errMsg)

      // Remove the incomplete assistant placeholder on error
      setMessages((prev) => prev.filter((m) => m.id !== assistantMsgId))
    } finally {
      setLoading(false)
      abortControllerRef.current = null
    }
  }

  const stop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
      setLoading(false)
    }
  }

  return {
    messages,
    input,
    setInput,
    sendMessage,
    stop,
    loading,
    error,
  }
}
