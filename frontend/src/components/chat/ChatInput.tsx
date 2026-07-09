import { useEffect, useRef } from 'react'
import { Send, Square, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

interface ChatInputProps {
  input: string
  setInput: (value: string) => void
  onSubmit: () => void
  onStop?: () => void
  loading: boolean
  disabled?: boolean
  error?: string | null
}

export default function ChatInput({
  input,
  setInput,
  onSubmit,
  onStop,
  loading,
  disabled = false,
  error = null,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  // Auto-resize height based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      const newHeight = Math.min(textareaRef.current.scrollHeight, 160) // max 160px
      textareaRef.current.style.height = `${newHeight}px`
    }
  }, [input])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (input.trim() && !loading && !disabled) {
        onSubmit()
      }
    }
  }

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !loading && !disabled) {
      onSubmit()
    }
  }

  return (
    <footer className="border-t border-slate-800 bg-slate-950/60 p-4 backdrop-blur-xl shrink-0">
      <div className="max-w-3xl mx-auto space-y-2">
        {error && (
          <div className="flex items-center gap-2 rounded-lg bg-red-950/40 border border-red-800/40 px-3 py-2 text-xs text-red-400 animate-in fade-in">
            <AlertCircle size={14} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form
          onSubmit={handleFormSubmit}
          className="relative flex items-end gap-2 rounded-xl border border-slate-800 bg-slate-900/90 p-2 shadow-lg focus-within:border-slate-600 transition-colors"
        >
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about company SEC filings, risks, financials..."
            disabled={disabled}
            rows={1}
            className="min-h-[36px] max-h-[160px] w-full resize-none border-0 bg-transparent py-1.5 px-2 text-sm text-white placeholder-slate-500 focus-visible:ring-0 focus-visible:outline-none scroller leading-relaxed"
          />

          <div className="flex shrink-0 items-center pb-0.5">
            {loading ? (
              <Button
                type="button"
                onClick={onStop}
                className="h-8 gap-1.5 rounded-lg bg-red-950/80 hover:bg-red-900 border border-red-800 text-red-300 px-3 text-xs font-semibold transition-all shadow-sm"
                title="Stop generation"
              >
                <Square size={13} className="fill-current" />
                <span>Stop</span>
              </Button>
            ) : (
              <Button
                type="submit"
                disabled={!input.trim() || disabled}
                className="h-8 rounded-lg bg-white text-slate-950 hover:bg-slate-200 disabled:bg-slate-800 disabled:text-slate-600 px-3 transition-all shadow-sm flex items-center justify-center"
                title="Send message (Enter)"
              >
                <Send size={15} />
              </Button>
            )}
          </div>
        </form>

        <div className="flex items-center justify-between px-2 text-[11px] text-slate-500 select-none">
          <span>Press <kbd className="font-mono text-slate-400 bg-slate-900 px-1 py-0.5 rounded border border-slate-800">Enter</kbd> to send, <kbd className="font-mono text-slate-400 bg-slate-900 px-1 py-0.5 rounded border border-slate-800">Shift + Enter</kbd> for new line</span>
          <span>Grounded with hybrid vector & lexical retrieval</span>
        </div>
      </div>
    </footer>
  )
}
