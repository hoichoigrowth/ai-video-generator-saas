import React from 'react'
import { UserGroupIcon } from '@heroicons/react/24/outline'

const CharacterRoster: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Character Roster & Detail Editor</h1>
        <p className="text-gray-600 mt-1">
          Manage character profiles, descriptions, and details
        </p>
      </div>
      
      <div className="workspace-card p-12 text-center">
        <UserGroupIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Character Management
        </h3>
        <p className="text-gray-600">
          Character roster, profile editing, and character relationship management tools.
        </p>
      </div>
    </div>
  )
}

export default CharacterRoster