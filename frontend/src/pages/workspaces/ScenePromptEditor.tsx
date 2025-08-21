import React from 'react'
import { PencilSquareIcon } from '@heroicons/react/24/outline'

const ScenePromptEditor: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Scene Prompt Editor</h1>
        <p className="text-gray-600 mt-1">
          Edit and refine scene generation prompts for AI image creation
        </p>
      </div>
      
      <div className="workspace-card p-12 text-center">
        <PencilSquareIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Scene Prompt Editor
        </h3>
        <p className="text-gray-600">
          Advanced prompt editing tools for scene generation, prompt templates, and AI image generation controls.
        </p>
      </div>
    </div>
  )
}

export default ScenePromptEditor