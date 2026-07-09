import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { AlertCircle, ArrowDown, FileText } from 'lucide-react'
import { api, type Message } from '@/lib/api'
import { useChat } from '@/hooks/useChat'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'

export default function ChatRoom() {
  const { threadId } = useParams<{ threadId: string }>()
  const [history, setHistory] = useState<Message[]>([])
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [historyError, setHistoryError] = useState<string | null>(null)
  const [showScrollButton, setShowScrollButton] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const scrollContainerRef = useRef<HTMLDivElement | null>(null)

  // Fetch thread messages from API
  useEffect(() => {
    if (!threadId) return

    setLoadingHistory(true)
    setHistoryError(null)
    api.messages
      .list(threadId)
      .then((data) => {
        setHistory(data || [])
      })
      .catch((err) => {
        console.error('Failed to load messages:', err)
        setHistoryError('Could not load chat history.')
      })
      .finally(() => {
        setLoadingHistory(false)
      })
  }, [threadId])

  // Consume the custom useChat hook
  const { messages, input, setInput, sendMessage, stop, loading, error } = useChat({
    threadId: threadId || '',
    initialMessages: history,
  })

  // Scroll to bottom helper
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    setShowScrollButton(false)
  }

  // Scroll on message updates or loading state changes if at bottom
  useEffect(() => {
    if (!showScrollButton) {
      messagesEndRef.current?.scrollIntoView({ behavior: loading ? 'auto' : 'smooth' })
    }
  }, [messages, loading, showScrollButton])

  // Handle scroll position to toggle floating button
  const handleScroll = () => {
    if (!scrollContainerRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 150
    setShowScrollButton(!isAtBottom && messages.length > 0)
  }

  if (!threadId) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center p-8 text-center text-slate-500 bg-slate-950">
        <div className="rounded-2xl bg-slate-900 p-4 border border-slate-800 mb-4 text-slate-400">
          <FileText size={32} />
        </div>
        <h2 className="text-lg font-bold text-slate-300 tracking-tight">No Workspace Selected</h2>
        <p className="mt-1 text-xs text-slate-500 max-w-xs">
          Select an existing conversation from the sidebar or start a new analysis session.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden h-full relative">
      {/* Thread Title Header */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-800 bg-slate-950/60 px-6 backdrop-blur-xl z-10">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500" title="Connected" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Analyst Workspace • <span className="text-white font-mono">{threadId.slice(0, 8)}</span>
          </h2>
        </div>
      </header>

      {/* Message Feed Area */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto scroller px-6 py-4 space-y-4 relative"
      >
        {loadingHistory ? (
          <div className="flex h-full items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-700 border-t-white" />
          </div>
        ) : historyError ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-red-400">
            <AlertCircle size={32} />
            <p className="text-sm">{historyError}</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center p-8 text-slate-500">
            <div className="rounded-2xl bg-slate-900/90 p-5 border border-slate-800 mb-5 text-white shadow-2xl max-w-sm w-full">
              <div className="h-8 w-8 rounded bg-white text-slate-950 flex items-center justify-center font-black text-sm mx-auto mb-3">
                DC
              </div>
              <h3 className="text-sm font-bold text-white tracking-tight">SEC Filing Copilot</h3>
              <p className="text-[11px] text-slate-400 mt-1 leading-normal">
                Hybrid RRF vector & keyword retrieval grounded in your Postgres document database.
              </p>
            </div>
            <h3 className="text-base font-bold text-slate-200 tracking-tight">
              How can I assist your financial research today?
            </h3>
            <p className="mt-1 max-w-md text-xs text-slate-400 leading-relaxed">
              Ask questions about company filings, financial performance, risk factors, or capital resources.
            </p>

            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
              {[
                'What are the primary risk factors disclosed in the latest filing?',
                'Summarize the liquidity and capital resources section.',
                'What are the key revenue drivers reported this fiscal year?',
                'Compare debt obligations and financing arrangements.',
              ].map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setInput(suggestion)
                  }}
                  className="text-left p-3 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:bg-slate-800/80 hover:border-slate-700 text-xs text-slate-300 transition-all shadow-sm"
                >
                  "{suggestion}"
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto pb-6">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Floating Scroll-to-Bottom Button */}
      {showScrollButton && (
        <div className="absolute bottom-24 right-8 z-20">
          <button
            onClick={scrollToBottom}
            className="flex items-center gap-1.5 rounded-full border border-slate-700 bg-slate-900/90 px-3 py-1.5 text-xs font-semibold text-white shadow-2xl backdrop-blur-md transition-all hover:bg-slate-800 hover:border-slate-500 animate-in fade-in slide-in-from-bottom-2"
            title="Scroll to latest message"
          >
            <ArrowDown size={13} className="animate-bounce" />
            <span>Latest messages</span>
          </button>
        </div>
      )}

      {/* New Modular ChatInput */}
      <ChatInput
        input={input}
        setInput={setInput}
        onSubmit={sendMessage}
        onStop={stop}
        loading={loading}
        disabled={loadingHistory || !!historyError}
        error={error}
      />
    </div>
  )
}

