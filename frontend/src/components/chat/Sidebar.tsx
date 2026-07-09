import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { MessageSquare, Plus, Trash2, LogOut, PanelLeft } from 'lucide-react'
import { api, type Thread } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

interface SidebarProps {
  onRefreshTrigger?: () => void
  isSidebarOpen?: boolean
  onToggleSidebar?: () => void
}

export default function Sidebar({ onRefreshTrigger, isSidebarOpen, onToggleSidebar }: SidebarProps) {
  const { threadId } = useParams<{ threadId: string }>()
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [threads, setThreads] = useState<Thread[]>([])
  const [loading, setLoading] = useState(true)

  const isOpen = isSidebarOpen ?? true

  const fetchThreads = async () => {
    try {
      const data = await api.threads.list()
      setThreads(data || [])
    } catch (err) {
      console.error('Failed to load chat history:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchThreads()

    const handleRefresh = () => {
      fetchThreads()
    }
    window.addEventListener('chat:refresh-threads', handleRefresh)
    return () => window.removeEventListener('chat:refresh-threads', handleRefresh)
  }, [threadId])

  const handleCreateThread = async () => {
    try {
      const newThread = await api.threads.create('New Conversation')
      if (newThread?.id) {
        navigate(`/chat/${newThread.id}`)
        if (onRefreshTrigger) onRefreshTrigger()
      }
    } catch (err) {
      console.error('Failed to create new chat thread:', err)
    }
  }

  const handleDeleteThread = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    e.preventDefault()
    if (!confirm('Are you sure you want to delete this conversation?')) return

    try {
      await api.threads.delete(id)
      setThreads((prev) => prev.filter((t) => t.id !== id))
      if (threadId === id) {
        navigate('/')
      }
      if (onRefreshTrigger) onRefreshTrigger()
    } catch (err) {
      console.error('Failed to delete chat thread:', err)
    }
  }

  return (
    <aside
      className={`flex h-full flex-col border-r border-slate-800 bg-slate-900/80 backdrop-blur-xl transition-all duration-300 ease-in-out shrink-0 z-20 ${
        isOpen ? 'w-80' : 'w-16'
      }`}
    >
      {/* Sidebar Header */}
      <div className="p-3 border-b border-slate-800 flex flex-col gap-3">
        <div className={`flex items-center ${isOpen ? 'justify-between' : 'justify-center'} px-1`}>
          {isOpen && (
            <div className="flex items-center gap-2 font-bold text-sm tracking-tight text-white truncate">
              <div className="h-6 w-6 rounded bg-white text-slate-950 flex items-center justify-center text-xs font-black shrink-0">
                DC
              </div>
              <span>Document Copilot</span>
            </div>
          )}
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={onToggleSidebar}
                className="p-1.5 rounded-md text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
                aria-label={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
              >
                <PanelLeft size={18} />
              </button>
            </TooltipTrigger>
            <TooltipContent side="right">
              {isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            </TooltipContent>
          </Tooltip>
        </div>

        {/* New Chat Button */}
        {isOpen ? (
          <Button
            onClick={handleCreateThread}
            className="w-full justify-start gap-2 bg-white font-semibold text-slate-950 hover:bg-slate-200 transition-all shadow-sm"
          >
            <Plus size={18} />
            <span>New Chat</span>
          </Button>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                onClick={handleCreateThread}
                size="icon"
                className="w-full h-9 bg-white text-slate-950 hover:bg-slate-200 transition-all shadow-sm flex items-center justify-center"
                aria-label="New Chat"
              >
                <Plus size={18} />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">New Chat</TooltipContent>
          </Tooltip>
        )}
      </div>

      {/* Scrollable Conversation List */}
      <div className="flex-1 overflow-y-auto scroller px-2 py-3 space-y-1">
        {isOpen && (
          <h3 className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Conversations
          </h3>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-700 border-t-white" />
          </div>
        ) : threads.length === 0 ? (
          isOpen ? (
            <p className="px-3 py-4 text-xs text-slate-500 italic text-center">No conversations yet.</p>
          ) : null
        ) : (
          threads.map((thread) => {
            const isActive = thread.id === threadId
            const title = thread.title || 'Untitled Conversation'

            const content = (
              <div
                key={thread.id}
                onClick={() => navigate(`/chat/${thread.id}`)}
                className={`group relative flex cursor-pointer items-center justify-between rounded-lg px-3 py-2.5 transition-all hover:bg-slate-800/80 ${
                  isActive ? 'bg-slate-800 text-white font-medium shadow-sm' : 'text-slate-400 hover:text-slate-200'
                } ${!isOpen ? 'justify-center px-0' : ''}`}
              >
                <div className={`flex items-center gap-2.5 min-w-0 ${isOpen ? 'pr-6' : ''}`}>
                  <MessageSquare
                    size={16}
                    className={
                      isActive
                        ? 'text-white shrink-0'
                        : 'text-slate-500 shrink-0 group-hover:text-slate-300'
                    }
                  />
                  {isOpen && <span className="truncate text-xs leading-5">{title}</span>}
                </div>

                {/* Delete Button on Hover (only when expanded) */}
                {isOpen && (
                  <button
                    onClick={(e) => handleDeleteThread(e, thread.id)}
                    className="absolute right-2 opacity-0 transition-opacity duration-200 text-slate-500 hover:text-red-400 group-hover:opacity-100 p-1"
                    aria-label="Delete conversation"
                    title="Delete conversation"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            )

            return isOpen ? (
              <div key={thread.id}>{content}</div>
            ) : (
              <Tooltip key={thread.id}>
                <TooltipTrigger asChild>{content}</TooltipTrigger>
                <TooltipContent side="right" className="max-w-[200px] truncate">
                  {title}
                </TooltipContent>
              </Tooltip>
            )
          })
        )}
      </div>

      {/* User profile footer section */}
      <div className="mt-auto border-t border-slate-800 p-3 bg-slate-950/40">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className={`flex items-center gap-3 w-full rounded-lg p-1.5 text-left transition-colors hover:bg-slate-800/80 ${
                !isOpen ? 'justify-center' : ''
              }`}
            >
              <Avatar className="h-8 w-8 border border-slate-700 shrink-0 bg-slate-800">
                <AvatarFallback className="bg-slate-800 text-white text-xs font-semibold">
                  {user?.email ? user.email.substring(0, 2).toUpperCase() : 'AN'}
                </AvatarFallback>
              </Avatar>
              {isOpen && (
                <div className="min-w-0 flex-1 pr-1">
                  <p className="truncate text-xs font-medium text-slate-200">{user?.email}</p>
                  <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
                    Analyst
                  </p>
                </div>
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            side="right"
            align="end"
            className="w-56 border-slate-800 bg-slate-900 text-slate-200"
          >
            <DropdownMenuLabel className="text-xs">
              <p className="font-medium text-white">{user?.email}</p>
              <p className="text-[10px] text-slate-500 font-normal mt-0.5">
                Financial Analyst Workspace
              </p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-slate-800" />
            <DropdownMenuItem
              onClick={signOut}
              className="text-red-400 focus:bg-red-950/50 focus:text-red-300 cursor-pointer gap-2 text-xs py-2"
            >
              <LogOut size={14} />
              <span>Sign Out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  )
}

