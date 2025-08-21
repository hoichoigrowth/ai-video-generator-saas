import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { 
  DocumentTextIcon, 
  PlusIcon, 
  ArrowPathIcon,
  CheckIcon,
  XMarkIcon,
  EyeIcon,
  PencilSquareIcon
} from '@heroicons/react/24/outline'
import { useStore } from '@/store'
import apiService from '@/services/api'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const ScreenplayReview: React.FC = () => {
  const { currentProject, screenplays, setScreenplays, updateProject } = useStore()
  const [selectedScreenplay, setSelectedScreenplay] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState('')

  // Fetch screenplays
  const { data: screenplaysData, isLoading } = useQuery({
    queryKey: ['screenplays', currentProject?.id],
    queryFn: () => currentProject ? apiService.getScreenplays(currentProject.id) : null,
    enabled: !!currentProject,
    onSuccess: (data) => {
      if (data) {
        setScreenplays(data)
        if (data.length > 0 && !selectedScreenplay) {
          setSelectedScreenplay(data[0].id)
          setEditContent(data[0].content)
        }
      }
    },
  })

  // Merge screenplays mutation
  const mergeScreenplaysMutation = useMutation({
    mutationFn: ({ screenplayIds }: { screenplayIds: string[] }) =>
      apiService.mergeScreenplays(currentProject!.id, screenplayIds),
    onSuccess: (data) => {
      toast.success('Screenplays merged successfully!')
      setScreenplays([...screenplays, data])
      setSelectedScreenplay(data.id)
    },
  })

  // Generate shot division mutation
  const generateShotDivisionMutation = useMutation({
    mutationFn: ({ screenplayId, agent }: { screenplayId: string; agent: string }) =>
      apiService.generateShotDivision(currentProject!.id, screenplayId, agent),
    onSuccess: () => {
      toast.success('Shot division generation started!')
      updateProject(currentProject!.id, {
        current_stage: 'shot_division',
        status: 'processing',
      })
    },
  })

  const handleSelectScreenplay = (screenplay: any) => {
    setSelectedScreenplay(screenplay.id)
    setEditContent(screenplay.content)
    setIsEditing(false)
  }

  const handleSaveChanges = () => {
    // TODO: Implement update screenplay API
    toast.success('Screenplay updated!')
    setIsEditing(false)
  }

  const handleProceedToShotDivision = () => {
    if (!selectedScreenplay) {
      toast.error('Please select a screenplay first')
      return
    }

    generateShotDivisionMutation.mutate({
      screenplayId: selectedScreenplay,
      agent: 'openai',
    })
  }

  const selectedScreenplayData = screenplays.find(s => s.id === selectedScreenplay)

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Project Selected
          </h3>
          <p className="text-gray-600">
            Please select a project to review screenplays.
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
          <h1 className="text-2xl font-bold text-gray-900">Screenplay Review & Editor</h1>
          <p className="text-gray-600 mt-1">
            Review AI-generated screenplays and proceed to shot division
          </p>
        </div>
        
        <div className="flex space-x-3">
          {screenplays.length > 1 && (
            <button
              onClick={() => mergeScreenplaysMutation.mutate({ 
                screenplayIds: screenplays.map(s => s.id) 
              })}
              disabled={mergeScreenplaysMutation.isPending}
              className="btn-secondary flex items-center space-x-2"
            >
              <PlusIcon className="w-5 h-5" />
              <span>Merge All</span>
            </button>
          )}
          
          {selectedScreenplay && (
            <button
              onClick={handleProceedToShotDivision}
              disabled={generateShotDivisionMutation.isPending}
              className="btn-primary flex items-center space-x-2"
            >
              <ArrowPathIcon className="w-5 h-5" />
              <span>Generate Shot Division</span>
            </button>
          )}
        </div>
      </div>

      {screenplays.length === 0 ? (
        <div className="workspace-card p-12 text-center">
          <DocumentTextIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            No Screenplays Yet
          </h3>
          <p className="text-gray-600 mb-6">
            Upload a script first to generate screenplays with AI
          </p>
          <button className="btn-primary">
            Go to Script Upload
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Screenplay List */}
          <div className="workspace-card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Generated Screenplays ({screenplays.length})
            </h2>
            
            <div className="space-y-3">
              {screenplays.map((screenplay) => (
                <div
                  key={screenplay.id}
                  className={clsx(
                    'p-4 rounded-lg border cursor-pointer transition-all duration-200',
                    selectedScreenplay === screenplay.id
                      ? 'border-primary-300 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  )}
                  onClick={() => handleSelectScreenplay(screenplay)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-medium text-gray-900 truncate">
                      {screenplay.title || `Version ${screenplay.version}`}
                    </h3>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                      {screenplay.agent_name}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                    {screenplay.content.substring(0, 100)}...
                  </p>
                  
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{screenplay.content.length} characters</span>
                    <span>{new Date(screenplay.generated_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Screenplay Content */}
          <div className="lg:col-span-2 workspace-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                {selectedScreenplayData?.title || 'Screenplay Content'}
              </h2>
              
              <div className="flex space-x-2">
                <button
                  onClick={() => setIsEditing(!isEditing)}
                  className="btn-secondary flex items-center space-x-2"
                >
                  {isEditing ? <EyeIcon className="w-5 h-5" /> : <PencilSquareIcon className="w-5 h-5" />}
                  <span>{isEditing ? 'Preview' : 'Edit'}</span>
                </button>
                
                {isEditing && (
                  <button
                    onClick={handleSaveChanges}
                    className="btn-primary flex items-center space-x-2"
                  >
                    <CheckIcon className="w-5 h-5" />
                    <span>Save</span>
                  </button>
                )}
              </div>
            </div>

            {selectedScreenplayData && (
              <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Agent:</span>
                    <p className="text-gray-600">{selectedScreenplayData.agent_name}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Version:</span>
                    <p className="text-gray-600">{selectedScreenplayData.version}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Generated:</span>
                    <p className="text-gray-600">
                      {new Date(selectedScreenplayData.generated_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {isEditing ? (
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full h-96 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm resize-none"
                placeholder="Edit screenplay content..."
              />
            ) : (
              <div className="h-96 overflow-y-auto custom-scrollbar">
                {editContent ? (
                  <div className="whitespace-pre-wrap font-mono text-sm text-gray-800 p-4 bg-gray-50 rounded-lg">
                    {editContent}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                      <DocumentTextIcon className="w-12 h-12 mx-auto mb-4" />
                      <p>Select a screenplay to view content</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Processing Status */}
      {generateShotDivisionMutation.isPending && (
        <div className="workspace-card p-6">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
            <div>
              <p className="font-medium text-gray-900">Generating Shot Division</p>
              <p className="text-sm text-gray-600">
                AI is analyzing the screenplay and creating optimal shot divisions...
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ScreenplayReview