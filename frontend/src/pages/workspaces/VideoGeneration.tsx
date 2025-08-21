import React from 'react'
import { PlayIcon, FilmIcon, CloudArrowDownIcon, ShareIcon } from '@heroicons/react/24/outline'
import { useStore } from '@/store'
import { useMutation } from '@tanstack/react-query'
import apiService from '@/services/api'
import toast from 'react-hot-toast'

const VideoGeneration: React.FC = () => {
  const { currentProject, updateProject } = useStore()

  // Generate video mutation
  const generateVideoMutation = useMutation({
    mutationFn: () => apiService.generateVideo(currentProject!.id),
    onSuccess: () => {
      toast.success('Video generation started!')
      updateProject(currentProject!.id, {
        status: 'processing',
        current_stage: 'video_generation',
      })
    },
  })

  const handleGenerateVideo = () => {
    if (!currentProject) {
      toast.error('Please select a project first')
      return
    }
    generateVideoMutation.mutate()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Video Generation Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Generate and manage your final AI-powered videos
          </p>
        </div>
        
        <button
          onClick={handleGenerateVideo}
          disabled={generateVideoMutation.isPending || !currentProject}
          className="btn-primary flex items-center space-x-2"
        >
          <PlayIcon className="w-5 h-5" />
          <span>Generate Final Video</span>
        </button>
      </div>

      {/* Generation Status */}
      {generateVideoMutation.isPending && (
        <div className="workspace-card p-6">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
            <div>
              <p className="font-medium text-gray-900">Generating Video</p>
              <p className="text-sm text-gray-600">
                AI is creating your final video using Kling AI technology...
              </p>
            </div>
          </div>
          
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-primary-600 h-2 rounded-full animate-pulse w-1/3" />
            </div>
          </div>
        </div>
      )}

      {/* Video Generation Options */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="workspace-card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Generation Settings</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Video Quality
              </label>
              <select className="input-field">
                <option value="standard">Standard (720p)</option>
                <option value="high">High (1080p)</option>
                <option value="ultra">Ultra (4K)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Frame Rate
              </label>
              <select className="input-field">
                <option value="24">24 FPS (Cinematic)</option>
                <option value="30">30 FPS (Standard)</option>
                <option value="60">60 FPS (Smooth)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Aspect Ratio
              </label>
              <select className="input-field">
                <option value="16:9">16:9 (Landscape)</option>
                <option value="9:16">9:16 (Portrait)</option>
                <option value="1:1">1:1 (Square)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Audio Settings
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input type="checkbox" className="mr-2" />
                  <span className="text-sm">Include background music</span>
                </label>
                <label className="flex items-center">
                  <input type="checkbox" className="mr-2" />
                  <span className="text-sm">Add sound effects</span>
                </label>
                <label className="flex items-center">
                  <input type="checkbox" className="mr-2" />
                  <span className="text-sm">Generate voiceover</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <div className="workspace-card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Preview & Export</h2>
          
          <div className="space-y-4">
            <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
              <div className="text-center text-gray-500">
                <FilmIcon className="w-12 h-12 mx-auto mb-2" />
                <p>Video Preview</p>
                <p className="text-sm">Generate video to see preview</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <button className="btn-secondary flex items-center justify-center space-x-2">
                <CloudArrowDownIcon className="w-5 h-5" />
                <span>Download</span>
              </button>
              <button className="btn-secondary flex items-center justify-center space-x-2">
                <ShareIcon className="w-5 h-5" />
                <span>Share</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Video History */}
      <div className="workspace-card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Generated Videos</h2>
        
        <div className="text-center py-8 text-gray-500">
          <FilmIcon className="w-12 h-12 mx-auto mb-4" />
          <p>No videos generated yet</p>
          <p className="text-sm">Start by generating your first video</p>
        </div>
      </div>
    </div>
  )
}

export default VideoGeneration