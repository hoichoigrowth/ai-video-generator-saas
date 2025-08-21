import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { 
  FilmIcon, 
  PlayIcon, 
  PencilSquareIcon,
  TrashIcon,
  PlusIcon,
  ClockIcon,
  CameraIcon
} from '@heroicons/react/24/outline'
import { useStore } from '@/store'
import apiService from '@/services/api'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const ShotBreakdown: React.FC = () => {
  const { currentProject, shots, setShots, updateProject } = useStore()
  const [selectedShotId, setSelectedShotId] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)

  // Fetch shot divisions and shots
  const { data: shotDivisionsData, isLoading } = useQuery({
    queryKey: ['shot-divisions', currentProject?.id],
    queryFn: () => currentProject ? apiService.getShotDivisions(currentProject.id) : null,
    enabled: !!currentProject,
  })

  const { data: shotsData } = useQuery({
    queryKey: ['shots', currentProject?.id, shotDivisionsData?.[0]?.id],
    queryFn: () => 
      currentProject && shotDivisionsData?.[0] 
        ? apiService.getShots(currentProject.id, shotDivisionsData[0].id) 
        : null,
    enabled: !!currentProject && !!shotDivisionsData?.[0],
    onSuccess: (data) => {
      if (data) {
        setShots(data)
        if (data.length > 0 && !selectedShotId) {
          setSelectedShotId(data[0].id)
        }
      }
    },
  })

  // Extract characters mutation
  const extractCharactersMutation = useMutation({
    mutationFn: ({ screenplayId }: { screenplayId: string }) =>
      apiService.extractCharacters(currentProject!.id, screenplayId),
    onSuccess: () => {
      toast.success('Character extraction started!')
      updateProject(currentProject!.id, {
        current_stage: 'character_design',
      })
    },
  })

  const selectedShot = shots.find(shot => shot.id === selectedShotId)
  const currentShotDivision = shotDivisionsData?.[0]

  const getTotalDuration = () => {
    return shots.reduce((total, shot) => total + shot.duration, 0)
  }

  const getCameraAngleColor = (angle: string) => {
    const colors: Record<string, string> = {
      'wide': 'bg-blue-100 text-blue-800',
      'medium': 'bg-green-100 text-green-800',
      'close-up': 'bg-yellow-100 text-yellow-800',
      'extreme-close-up': 'bg-red-100 text-red-800',
      'overhead': 'bg-purple-100 text-purple-800',
    }
    return colors[angle.toLowerCase()] || 'bg-gray-100 text-gray-800'
  }

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <FilmIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Project Selected
          </h3>
          <p className="text-gray-600">
            Please select a project to view shot breakdowns.
          </p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/3" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="h-96 bg-gray-200 rounded" />
          <div className="lg:col-span-2 h-96 bg-gray-200 rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Shot Breakdown Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Manage and edit shot divisions for your video production
          </p>
        </div>
        
        <div className="flex space-x-3">
          {currentShotDivision && (
            <button
              onClick={() => extractCharactersMutation.mutate({ 
                screenplayId: currentShotDivision.screenplay_id 
              })}
              disabled={extractCharactersMutation.isPending}
              className="btn-primary flex items-center space-x-2"
            >
              <PlayIcon className="w-5 h-5" />
              <span>Extract Characters</span>
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="workspace-card p-4">
          <div className="flex items-center">
            <FilmIcon className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Total Shots</p>
              <p className="text-xl font-bold text-gray-900">{shots.length}</p>
            </div>
          </div>
        </div>
        
        <div className="workspace-card p-4">
          <div className="flex items-center">
            <ClockIcon className="w-8 h-8 text-green-600 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Total Duration</p>
              <p className="text-xl font-bold text-gray-900">{getTotalDuration()}s</p>
            </div>
          </div>
        </div>
        
        <div className="workspace-card p-4">
          <div className="flex items-center">
            <CameraIcon className="w-8 h-8 text-purple-600 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Camera Angles</p>
              <p className="text-xl font-bold text-gray-900">
                {new Set(shots.map(s => s.camera_angle)).size}
              </p>
            </div>
          </div>
        </div>
        
        <div className="workspace-card p-4">
          <div className="flex items-center">
            <PlayIcon className="w-8 h-8 text-red-600 mr-3" />
            <div>
              <p className="text-sm text-gray-600">Avg Duration</p>
              <p className="text-xl font-bold text-gray-900">
                {shots.length > 0 ? Math.round(getTotalDuration() / shots.length) : 0}s
              </p>
            </div>
          </div>
        </div>
      </div>

      {shots.length === 0 ? (
        <div className="workspace-card p-12 text-center">
          <FilmIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            No Shot Division Yet
          </h3>
          <p className="text-gray-600 mb-6">
            Generate a screenplay first, then create shot divisions
          </p>
          <button className="btn-primary">
            Go to Screenplay Review
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Shots List */}
          <div className="workspace-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Shots ({shots.length})
              </h2>
              <button className="btn-secondary text-sm">
                <PlusIcon className="w-4 h-4 mr-1" />
                Add Shot
              </button>
            </div>
            
            <div className="space-y-3 max-h-96 overflow-y-auto custom-scrollbar">
              {shots.map((shot) => (
                <div
                  key={shot.id}
                  className={clsx(
                    'p-4 rounded-lg border cursor-pointer transition-all duration-200',
                    selectedShotId === shot.id
                      ? 'border-primary-300 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  )}
                  onClick={() => setSelectedShotId(shot.id)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-gray-900">
                      Shot {shot.shot_number}
                    </h3>
                    <span className={clsx(
                      'text-xs px-2 py-1 rounded-full',
                      getCameraAngleColor(shot.camera_angle)
                    )}>
                      {shot.camera_angle}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                    {shot.description}
                  </p>
                  
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{shot.duration}s</span>
                    <span>{shot.characters.length} characters</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Shot Details */}
          <div className="lg:col-span-2 workspace-card p-6">
            {selectedShot ? (
              <>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <h2 className="text-xl font-semibold text-gray-900">
                      Shot {selectedShot.shot_number}
                    </h2>
                    <span className={clsx(
                      'px-2 py-1 text-sm rounded-full',
                      getCameraAngleColor(selectedShot.camera_angle)
                    )}>
                      {selectedShot.camera_angle}
                    </span>
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setIsEditing(!isEditing)}
                      className="btn-secondary flex items-center space-x-2"
                    >
                      <PencilSquareIcon className="w-5 h-5" />
                      <span>{isEditing ? 'Cancel' : 'Edit'}</span>
                    </button>
                    <button className="btn-danger flex items-center space-x-2">
                      <TrashIcon className="w-5 h-5" />
                      <span>Delete</span>
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Shot Information */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      {isEditing ? (
                        <textarea
                          defaultValue={selectedShot.description}
                          className="textarea-field"
                          rows={3}
                        />
                      ) : (
                        <p className="text-gray-900 p-3 bg-gray-50 rounded-lg">
                          {selectedShot.description}
                        </p>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Duration
                        </label>
                        {isEditing ? (
                          <input
                            type="number"
                            defaultValue={selectedShot.duration}
                            className="input-field"
                          />
                        ) : (
                          <p className="text-gray-900 p-2 bg-gray-50 rounded">
                            {selectedShot.duration} seconds
                          </p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Camera Angle
                        </label>
                        {isEditing ? (
                          <select
                            defaultValue={selectedShot.camera_angle}
                            className="input-field"
                          >
                            <option value="wide">Wide Shot</option>
                            <option value="medium">Medium Shot</option>
                            <option value="close-up">Close-up</option>
                            <option value="extreme-close-up">Extreme Close-up</option>
                            <option value="overhead">Overhead</option>
                          </select>
                        ) : (
                          <p className="text-gray-900 p-2 bg-gray-50 rounded">
                            {selectedShot.camera_angle}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Location
                        </label>
                        {isEditing ? (
                          <input
                            type="text"
                            defaultValue={selectedShot.location}
                            className="input-field"
                          />
                        ) : (
                          <p className="text-gray-900 p-2 bg-gray-50 rounded">
                            {selectedShot.location || 'Not specified'}
                          </p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Time of Day
                        </label>
                        {isEditing ? (
                          <select
                            defaultValue={selectedShot.time_of_day}
                            className="input-field"
                          >
                            <option value="morning">Morning</option>
                            <option value="afternoon">Afternoon</option>
                            <option value="evening">Evening</option>
                            <option value="night">Night</option>
                          </select>
                        ) : (
                          <p className="text-gray-900 p-2 bg-gray-50 rounded">
                            {selectedShot.time_of_day || 'Not specified'}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Characters & Dialogue */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Characters
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {selectedShot.characters.map((character, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                          >
                            {character}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Dialogue
                      </label>
                      {isEditing ? (
                        <textarea
                          defaultValue={selectedShot.dialogue}
                          className="textarea-field"
                          rows={4}
                        />
                      ) : (
                        <div className="p-3 bg-gray-50 rounded-lg max-h-32 overflow-y-auto">
                          <p className="text-gray-900 whitespace-pre-wrap">
                            {selectedShot.dialogue || 'No dialogue'}
                          </p>
                        </div>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Action
                      </label>
                      {isEditing ? (
                        <textarea
                          defaultValue={selectedShot.action}
                          className="textarea-field"
                          rows={3}
                        />
                      ) : (
                        <div className="p-3 bg-gray-50 rounded-lg max-h-24 overflow-y-auto">
                          <p className="text-gray-900 whitespace-pre-wrap">
                            {selectedShot.action || 'No action description'}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {isEditing && (
                  <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-gray-200">
                    <button
                      onClick={() => setIsEditing(false)}
                      className="btn-secondary"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => {
                        // TODO: Implement update shot API
                        toast.success('Shot updated!')
                        setIsEditing(false)
                      }}
                      className="btn-primary"
                    >
                      Save Changes
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <FilmIcon className="w-12 h-12 mx-auto mb-4" />
                  <p>Select a shot to view details</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Processing Status */}
      {extractCharactersMutation.isPending && (
        <div className="workspace-card p-6">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
            <div>
              <p className="font-medium text-gray-900">Extracting Characters</p>
              <p className="text-sm text-gray-600">
                AI is analyzing shot divisions to identify and extract characters...
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ShotBreakdown