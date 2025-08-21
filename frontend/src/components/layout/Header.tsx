import React, { useState } from 'react'
import clsx from 'clsx'

const Header: React.FC = () => {
  const [notifications] = useState([
    { id: 1, message: 'Screenplay generation completed', time: '2 min ago', read: false },
    { id: 2, message: 'Character extraction finished', time: '5 min ago', read: true },
  ])
  const [showNotifications, setShowNotifications] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [currentWorkspace] = useState('dashboard')
  const [currentProject] = useState({ name: 'Demo Project' })
  const [isConnected] = useState(true)
  const [healthData] = useState({ status: 'healthy' })

  const getWorkspaceTitle = () => {
    const titles: Record<string, string> = {
      'dashboard': 'Project Dashboard',
      'script-upload': 'Script Upload & Editor',
      'screenplay-review': 'Screenplay Review & Editor',
      'shot-breakdown': 'Shot Breakdown Dashboard',
      'production-design': 'Production Design Hub',
      'character-roster': 'Character Roster & Editor',
      'character-gallery': 'Character Image Gallery',
      'scene-prompt-editor': 'Scene Prompt Editor',
      'scene-image-selector': 'Scene Image Selector',
      'video-generation': 'Video Generation Dashboard',
    }
    return titles[currentWorkspace] || 'AI Video Generator'
  }

  const unreadCount = notifications.filter(n => !n.read).length

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left section - Title and project info */}
          <div className="flex items-center space-x-4">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                {getWorkspaceTitle()}
              </h1>
              {currentProject && (
                <p className="text-sm text-gray-500 mt-1">
                  Project: {currentProject.name}
                </p>
              )}
            </div>
          </div>

          {/* Right section */}
          <div className="flex items-center space-x-4">
            {/* WebSocket Status */}
            <div className="flex items-center space-x-2">
              <svg 
                className={clsx(
                  'w-4 h-4',
                  isConnected ? 'text-green-500' : 'text-red-500'
                )}
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
              </svg>
              <span className={clsx(
                'text-xs font-medium',
                isConnected ? 'text-green-600' : 'text-red-600'
              )}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            {/* System Health */}
            <div className={clsx(
              'px-2 py-1 text-xs font-medium rounded-full',
              healthData?.status === 'healthy' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            )}>
              {healthData?.status === 'healthy' ? '✅ Healthy' : '❌ Issues'}
            </div>

            {/* Notifications */}
            <div className="relative">
              <button 
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2 text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5-5V9.5a4.5 4.5 0 00-9 0V12l-5 5h5m0 0v1a3 3 0 006 0v-1m-6 0h6" />
                </svg>
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </button>
              
              {showNotifications && (
                <div className="absolute right-0 z-10 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200">
                  <div className="p-4">
                    <h3 className="text-sm font-medium text-gray-900 mb-3">
                      Notifications
                    </h3>
                    <div className="space-y-2">
                      {notifications.map((notification) => (
                        <div
                          key={notification.id}
                          className={clsx(
                            'p-3 rounded-lg text-sm',
                            notification.read 
                              ? 'bg-gray-50 text-gray-700' 
                              : 'bg-blue-50 text-blue-900'
                          )}
                        >
                          <p className="font-medium">{notification.message}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {notification.time}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* User Menu */}
            <div className="relative">
              <button 
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 p-2 text-gray-700 hover:text-gray-900 transition-colors duration-200"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {showUserMenu && (
                <div className="absolute right-0 z-10 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200">
                  <div className="p-1">
                    <button className="flex items-center w-full px-3 py-2 text-sm rounded-lg transition-colors duration-200 hover:bg-gray-100 text-gray-700">
                      <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Profile
                    </button>
                    
                    <button className="flex items-center w-full px-3 py-2 text-sm rounded-lg transition-colors duration-200 hover:bg-gray-100 text-gray-700">
                      <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      Settings
                    </button>
                    
                    <div className="border-t border-gray-100 my-1" />
                    
                    <button className="flex items-center w-full px-3 py-2 text-sm rounded-lg transition-colors duration-200 hover:bg-red-50 text-red-700">
                      <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      Sign out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header