import React, { useState, useEffect, useMemo } from 'react'
import type { Message } from '@/lib/api'
import { Cpu, ShieldCheck, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export interface CitationData {
  ticker?: string
  fiscal_year?: number
  section_name?: string
  filing_type?: string
  chunk_id?: string
  exact_quote?: string
  title?: string
  source?: string
  page?: number
}

interface MessageBubbleProps {
  message: Message
}

/**
 * Recursively parse React children or strings and replace [n] markers with superscript citation badges.
 */
function renderChildrenWithBadges(
  children: React.ReactNode,
  citations: CitationData[],
  onCitationClick: (index: number) => void,
): React.ReactNode {
  if (typeof children === 'string') {
    const parts = children.split(/(\[\d+\])/g)
    return parts.map((part, i) => {
      const match = part.match(/^\[(\d+)\]$/)
      if (match) {
        const num = parseInt(match[1], 10)
        const hasCitation = num >= 1 && num <= citations.length
        return (
          <sup
            key={i}
            onClick={(e) => {
              e.stopPropagation()
              if (hasCitation) onCitationClick(num - 1)
            }}
            className={`inline-flex items-center justify-center ml-0.5 mr-0.5 min-w-[18px] h-[18px] rounded text-[10px] font-bold leading-none align-super cursor-pointer transition-colors ${
              hasCitation
                ? 'bg-slate-700 text-slate-200 hover:bg-slate-600 hover:text-white shadow-sm'
                : 'bg-slate-800 text-slate-500'
            }`}
            title={
              hasCitation
                ? `${citations[num - 1].ticker || 'Source'} ${citations[num - 1].fiscal_year ? `FY${citations[num - 1].fiscal_year}` : ''} — ${citations[num - 1].section_name || 'View source'}`
                : `Citation [${num}]`
            }
          >
            {num}
          </sup>
        )
      }
      return part
    })
  }

  if (Array.isArray(children)) {
    return React.Children.map(children, (child) =>
      renderChildrenWithBadges(child, citations, onCitationClick)
    )
  }

  if (React.isValidElement(children)) {
    if (children.type === 'code' || children.type === 'pre') {
      return children
    }
    const element = children as React.ReactElement<{ children?: React.ReactNode }>
    if (element.props && element.props.children !== undefined) {
      return React.cloneElement(element, {
        ...element.props,
        children: renderChildrenWithBadges(element.props.children, citations, onCitationClick),
      })
    }
  }

  return children
}

/** Compact academic-style reference list shown below assistant messages. */
function ReferenceList({
  citations,
  highlightedIndex,
}: {
  citations: CitationData[]
  highlightedIndex: number | null
}) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)

  useEffect(() => {
    if (highlightedIndex !== null) {
      setExpandedIdx(highlightedIndex)
    }
  }, [highlightedIndex])

  if (citations.length === 0) return null

  return (
    <div className="mt-5 border-t border-slate-800/60 pt-3">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">
        References
      </p>
      <ol className="space-y-1.5 list-none m-0 p-0">
        {citations.map((cite, idx) => {
          const ticker = cite.ticker || 'Source'
          const year = cite.fiscal_year ? `FY${cite.fiscal_year}` : ''
          const section = cite.section_name || ''
          const filingType = cite.filing_type || '10-K'
          const quote = cite.exact_quote
          const isHighlighted = highlightedIndex === idx
          const isExpanded = expandedIdx === idx

          return (
            <li
              key={idx}
              id={`ref-${idx}`}
              className={`rounded-md px-2.5 py-1.5 text-xs transition-colors ${
                isHighlighted ? 'bg-slate-800/80 ring-1 ring-slate-600' : ''
              }`}
            >
              <div className="flex items-start gap-2">
                <span className="shrink-0 font-bold text-slate-400 tabular-nums w-5 text-right">
                  [{idx + 1}]
                </span>
                <div className="min-w-0 flex-1">
                  <span className="font-semibold text-slate-200">{ticker}</span>
                  {year && <span className="text-slate-400 ml-1.5">{year}</span>}
                  {filingType && (
                    <span className="text-slate-500 ml-1.5">{filingType}</span>
                  )}
                  {section && (
                    <span className="text-slate-400 ml-1"> — {section}</span>
                  )}

                  {quote && (
                    <button
                      type="button"
                      onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                      className="ml-2 inline-flex items-center gap-0.5 text-slate-500 hover:text-slate-300 transition-colors"
                      aria-label={isExpanded ? 'Hide quote' : 'Show quote'}
                    >
                      {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    </button>
                  )}

                  {quote && isExpanded && (
                    <div className="mt-1.5 rounded bg-slate-950/60 border-l-2 border-slate-600 p-2 text-[11px] text-slate-400 italic leading-relaxed">
                      "{quote}"
                    </div>
                  )}
                </div>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const citations: CitationData[] = useMemo(
    () => message.citations || message.metadata_json?.citations || [],
    [message.citations, message.metadata_json],
  )
  const confidence = message.metadata_json?.confidence_summary
  const sufficient = message.metadata_json?.has_sufficient_evidence
  const [highlightedCitation, setHighlightedCitation] = useState<number | null>(null)

  const handleCitationClick = (index: number) => {
    setHighlightedCitation(index)
    // Scroll the reference into view
    const el = document.getElementById(`ref-${index}`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    // Clear highlight after a short delay
    setTimeout(() => setHighlightedCitation(null), 2500)
  }

  // ── User message: compact right-aligned bubble ──
  if (isUser) {
    return (
      <div className="flex w-full justify-end py-3">
        <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-slate-800 border border-slate-700 px-4 py-2.5 text-sm text-white leading-relaxed shadow-sm">
          <div className="whitespace-pre-wrap break-words">{message.content}</div>
          {message.created_at && (
            <div className="mt-1.5 text-[10px] text-slate-500 text-right select-none">
              {new Date(message.created_at).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </div>
          )}
        </div>
      </div>
    )
  }

  // ── Assistant message: full-width document-style layout ──
  return (
    <div className="w-full py-5">
      {/* Role header */}
      <div className="flex items-center gap-2 mb-3">
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-slate-800 border border-slate-700 text-white">
          <Cpu size={13} />
        </div>
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Copilot
        </span>
        {message.created_at && (
          <span className="text-[10px] text-slate-600 select-none ml-auto">
            {new Date(message.created_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        )}
      </div>

      {/* Prose content */}
      <div className="prose-invert text-sm text-slate-200 leading-7 max-w-none text-justify">
        {message.content ? (
          <>
            <Markdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => (
                  <p className="mb-4 text-justify leading-relaxed text-slate-200">
                    {renderChildrenWithBadges(children, citations, handleCitationClick)}
                  </p>
                ),
                li: ({ children }) => (
                  <li className="mb-1.5 text-justify leading-relaxed text-slate-300">
                    {renderChildrenWithBadges(children, citations, handleCitationClick)}
                  </li>
                ),
                td: ({ children }) => (
                  <td className="py-2 px-2 border-b border-slate-800/60 text-slate-300">
                    {renderChildrenWithBadges(children, citations, handleCitationClick)}
                  </td>
                ),
                th: ({ children }) => (
                  <th className="text-left py-2 px-2 border-b border-slate-700 text-slate-200 font-semibold">
                    {renderChildrenWithBadges(children, citations, handleCitationClick)}
                  </th>
                ),
                span: ({ children }) => (
                  <span>
                    {renderChildrenWithBadges(children, citations, handleCitationClick)}
                  </span>
                ),
                strong: ({ children }) => (
                  <strong className="text-white font-semibold">
                    {renderChildrenWithBadges(children, citations, handleCitationClick)}
                  </strong>
                ),
                em: ({ children }) => (
                  <em className="italic text-slate-300">
                    {renderChildrenWithBadges(children, citations, handleCitationClick)}
                  </em>
                ),
              }}
            >
              {message.content}
            </Markdown>
            {citations.length > 0 && !/\[\d+\]/.test(message.content) && (
              <div className="mt-4 flex flex-wrap items-center gap-1.5 pt-3 border-t border-slate-800/40 text-xs text-slate-400">
                <span className="font-semibold text-slate-400 mr-1">Inline sources for above passage:</span>
                {citations.map((cite, idx) => (
                  <sup
                    key={idx}
                    onClick={() => handleCitationClick(idx)}
                    className="inline-flex items-center justify-center min-w-[20px] h-[20px] rounded text-[11px] font-bold leading-none bg-slate-700 text-slate-200 hover:bg-slate-600 hover:text-white shadow-sm cursor-pointer transition-colors px-1.5"
                    title={`${cite.ticker || 'Source'} ${cite.fiscal_year ? `FY${cite.fiscal_year}` : ''} — ${cite.section_name || 'View source'}`}
                  >
                    {idx + 1}
                  </sup>
                ))}
              </div>
            )}
          </>

        ) : (
          <span className="text-slate-500 italic flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-pulse" />
            Analyzing filings...
          </span>
        )}
      </div>

      {/* Evidence assessment */}
      {confidence && (
        <div className="mt-4 flex items-start gap-2 rounded-lg bg-slate-900/60 border border-slate-800/60 p-2.5 text-xs text-slate-400">
          {sufficient === false ? (
            <AlertTriangle size={14} className="text-amber-400 shrink-0 mt-0.5" />
          ) : (
            <ShieldCheck size={14} className="text-slate-400 shrink-0 mt-0.5" />
          )}
          <div>
            <span className="font-semibold text-slate-300">Evidence: </span>
            <span>{confidence}</span>
          </div>
        </div>
      )}

      {/* Academic reference list */}
      <ReferenceList citations={citations} highlightedIndex={highlightedCitation} />
    </div>
  )
}
