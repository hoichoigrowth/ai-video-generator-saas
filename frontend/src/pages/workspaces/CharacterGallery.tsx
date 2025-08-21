import React from 'react'
import { PhotoIcon } from '@heroicons/react/24/outline'

const CharacterGallery: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Character Image Gallery</h1>
        <p className="text-gray-600 mt-1">
          Browse and select character images for your video production
        </p>
      </div>
      
      <div className="workspace-card p-12 text-center">
        <PhotoIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Character Image Gallery
        </h3>
        <p className="text-gray-600">
          Image gallery for character visualization, AI-generated character images, and image selection tools.
        </p>
      </div>
    </div>
  )
}

export default CharacterGallery