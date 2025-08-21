import React from 'react'
import { CameraIcon } from '@heroicons/react/24/outline'

const SceneImageSelector: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Scene Image Selector</h1>
        <p className="text-gray-600 mt-1">
          Browse and select generated scene images for video production
        </p>
      </div>
      
      <div className="workspace-card p-12 text-center">
        <CameraIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Scene Image Selection
        </h3>
        <p className="text-gray-600">
          Image gallery interface for scene selection, image comparison tools, and batch selection capabilities.
        </p>
      </div>
    </div>
  )
}

export default SceneImageSelector