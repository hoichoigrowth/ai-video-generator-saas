import React from 'react'
import { Cog6ToothIcon } from '@heroicons/react/24/outline'

const ProjectSettings: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Project Settings</h1>
        <p className="text-gray-600 mt-1">
          Configure your project settings and preferences
        </p>
      </div>
      
      <div className="workspace-card p-12 text-center">
        <Cog6ToothIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Project Settings
        </h3>
        <p className="text-gray-600">
          Project configuration, API settings, export preferences, and system configuration options.
        </p>
      </div>
    </div>
  )
}

export default ProjectSettings