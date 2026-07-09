import { useEffect, useState } from 'react'
import { createBrowserRouter, RouterProvider, Navigate, Outlet, useNavigate } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/lib/auth'
import { api } from '@/lib/api'
import { TooltipProvider } from '@/components/ui/tooltip'
import Login from '@/pages/Login'
import WorkspaceLayout from '@/components/chat/WorkspaceLayout'
import ChatRoom from '@/components/chat/ChatRoom'

// Component to protect routes requiring authentication
function ProtectedLayout() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-950 text-slate-200">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-700 border-t-white" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

// Redirects index '/' to the most recent thread, or displays empty state
function ThreadRedirector() {
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.threads
      .list()
      .then((threads) => {
        if (threads && threads.length > 0) {
          navigate(`/chat/${threads[0].id}`, { replace: true })
        } else {
          setLoading(false)
        }
      })
      .catch((err) => {
        console.error('Failed to list threads for redirection:', err)
        setLoading(false)
      })
  }, [navigate])

  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-slate-950 text-slate-200">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-700 border-t-white" />
      </div>
    )
  }

  return <ChatRoom />
}

const router = createBrowserRouter([
  // Public route
  {
    path: '/login',
    element: <Login />,
  },
  // Protected routes
  {
    element: <ProtectedLayout />,
    children: [
      {
        element: <WorkspaceLayout />,
        children: [
          {
            path: '/',
            element: <ThreadRedirector />,
          },
          {
            path: '/chat/:threadId',
            element: <ChatRoom />,
          },
        ],
      },
    ],
  },
  // Fallback
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
])

export default function App() {
  return (
    <AuthProvider>
      <TooltipProvider>
        <RouterProvider router={router} />
      </TooltipProvider>
    </AuthProvider>
  )
}

