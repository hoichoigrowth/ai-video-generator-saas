import React, { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import { useStore } from '@/store'
import websocketService from '@/services/websocket'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation()
  const { currentProject, setCurrentWorkspace } = useStore()

  useEffect(() => {
    // Update current workspace based on route
    const path = location.pathname
    if (path === '/') {
      setCurrentWorkspace('dashboard')
    } else {
      const workspace = path.split('/').pop() || 'dashboard'
      setCurrentWorkspace(workspace)
    }
  }, [location.pathname, setCurrentWorkspace])

  useEffect(() => {
    // Connect to WebSocket when project is selected
    if (currentProject?.id) {
      websocketService.connect(currentProject.id)
    }

    return () => {
      // Cleanup WebSocket connection
      websocketService.disconnect()
    }
  }, [currentProject?.id])

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <Header />
        
        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

export default Layout