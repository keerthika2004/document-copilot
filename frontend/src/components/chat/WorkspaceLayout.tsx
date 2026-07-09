import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export interface WorkspaceContextType {
  isSidebarOpen: boolean
  onToggleSidebar: () => void
}

export default function WorkspaceLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  const handleToggleSidebar = () => {
    setIsSidebarOpen((prev) => !prev)
  }

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden relative">
      {/* Subtle monochrome background pattern */}
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,#1e293b10_1px,transparent_1px),linear-gradient(to_bottom,#1e293b10_1px,transparent_1px)] bg-[size:3rem_3rem]" />

      {/* Collapsible Sidebar */}
      <Sidebar isSidebarOpen={isSidebarOpen} onToggleSidebar={handleToggleSidebar} />

      {/* Main Content Pane */}
      <main className="relative flex flex-1 flex-col min-w-0 overflow-hidden bg-slate-950/40 backdrop-blur-3xl">
        <Outlet context={{ isSidebarOpen, onToggleSidebar: handleToggleSidebar } satisfies WorkspaceContextType} />
      </main>
    </div>
  )
}

