import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  HomeIcon, 
  DocumentTextIcon, 
  FilmIcon, 
  CameraIcon, 
  UserGroupIcon, 
  PhotoIcon, 
  PencilSquareIcon, 
  PlayIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  CloudArrowUpIcon
} from '@heroicons/react/24/outline'
import { useStore } from '@/store'
import clsx from 'clsx'

const workspaces = [
  {
    id: 'dashboard',
    name: 'Dashboard',
    href: '/',
    icon: HomeIcon,
    description: 'Project overview',
  },
  {
    id: 'script-upload',
    name: 'Script Upload',
    href: '/workspace/script-upload',
    icon: CloudArrowUpIcon,
    description: 'Upload & edit scripts',
  },
  {
    id: 'screenplay-review',
    name: 'Screenplay Review',
    href: '/workspace/screenplay-review',
    icon: DocumentTextIcon,
    description: 'Review AI-generated screenplays',
  },
  {
    id: 'shot-breakdown',
    name: 'Shot Breakdown',
    href: '/workspace/shot-breakdown',
    icon: FilmIcon,
    description: 'Manage shot divisions',
  },
  {
    id: 'production-design',
    name: 'Production Design',
    href: '/workspace/production-design',
    icon: ChartBarIcon,
    description: 'Production planning hub',
  },
  {
    id: 'character-roster',
    name: 'Character Roster',
    href: '/workspace/character-roster',
    icon: UserGroupIcon,
    description: 'Manage characters',
  },
  {
    id: 'character-gallery',
    name: 'Character Gallery',
    href: '/workspace/character-gallery',
    icon: PhotoIcon,
    description: 'Character images',
  },
  {
    id: 'scene-prompt-editor',
    name: 'Scene Prompts',
    href: '/workspace/scene-prompt-editor',
    icon: PencilSquareIcon,
    description: 'Edit scene prompts',
  },
  {
    id: 'scene-image-selector',
    name: 'Scene Images',
    href: '/workspace/scene-image-selector',
    icon: CameraIcon,
    description: 'Select scene images',
  },
  {
    id: 'video-generation',
    name: 'Video Generation',
    href: '/workspace/video-generation',
    icon: PlayIcon,
    description: 'Generate final video',
  },
]

const Sidebar: React.FC = () => {
  const location = useLocation()
  const { currentProject, currentWorkspace } = useStore()

  const isWorkspaceAccessible = (workspaceId: string) => {
    if (!currentProject) return workspaceId === 'dashboard'
    
    const stageOrder = [
      'dashboard',
      'script-upload',
      'screenplay-review',
      'shot-breakdown',
      'production-design',
      'character-roster',
      'character-gallery',
      'scene-prompt-editor',
      'scene-image-selector',
      'video-generation',
    ]
    
    const currentStageIndex = stageOrder.indexOf(getWorkspaceFromStage(currentProject.current_stage))
    const workspaceIndex = stageOrder.indexOf(workspaceId)
    
    return workspaceIndex <= currentStageIndex + 1 // Allow access to current + next stage
  }

  const getWorkspaceFromStage = (stage: string) => {
    const stageMap: Record<string, string> = {
      'input': 'script-upload',
      'screenplay_generation': 'screenplay-review',
      'shot_division': 'shot-breakdown',
      'character_design': 'character-roster',
      'scene_generation': 'scene-prompt-editor',
      'video_generation': 'video-generation',
      'completed': 'video-generation',
    }
    return stageMap[stage] || 'dashboard'
  }

  return (
    <div className="w-64 bg-white shadow-sm border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <FilmIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">AI Video</h1>
            <p className="text-xs text-gray-500">Generator</p>
          </div>
        </div>
      </div>

      {/* Current Project Info */}
      {currentProject && (
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <h3 className="text-sm font-medium text-gray-900 truncate">
            {currentProject.name}
          </h3>
          <div className="flex items-center space-x-2 mt-1">
            <span className={clsx(
              'status-badge',
              {
                'status-pending': currentProject.status === 'created',
                'status-processing': currentProject.status === 'processing',
                'status-completed': currentProject.status === 'completed',
                'status-error': currentProject.status === 'error',
              }
            )}>
              {currentProject.status}
            </span>
            <span className="text-xs text-gray-500">
              {currentProject.current_stage.replace('_', ' ')}
            </span>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {workspaces.map((workspace) => {
          const isActive = location.pathname === workspace.href
          const isAccessible = isWorkspaceAccessible(workspace.id)
          
          return (
            <Link
              key={workspace.id}
              to={workspace.href}
              className={clsx(
                'group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200',
                {
                  'bg-primary-100 text-primary-900 border border-primary-200': isActive,
                  'text-gray-700 hover:bg-gray-100': !isActive && isAccessible,
                  'text-gray-400 cursor-not-allowed': !isAccessible,
                }
              )}
              onClick={(e) => {
                if (!isAccessible) {
                  e.preventDefault()
                }
              }}
            >
              <workspace.icon
                className={clsx(
                  'mr-3 h-5 w-5 flex-shrink-0',
                  {
                    'text-primary-600': isActive,
                    'text-gray-500 group-hover:text-gray-700': !isActive && isAccessible,
                    'text-gray-300': !isAccessible,
                  }
                )}
              />
              <div className="flex-1 min-w-0">
                <div className="truncate">{workspace.name}</div>
                <div className="text-xs text-gray-500 truncate">
                  {workspace.description}
                </div>
              </div>
              {!isAccessible && (
                <div className="w-2 h-2 bg-gray-300 rounded-full flex-shrink-0" />
              )}
            </Link>
          )
        })}
      </nav>

      {/* Settings */}
      <div className="p-4 border-t border-gray-200">
        <Link
          to="/project/settings"
          className="group flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-100 transition-colors duration-200"
        >
          <Cog6ToothIcon className="mr-3 h-5 w-5 text-gray-500 group-hover:text-gray-700" />
          Settings
        </Link>
      </div>
    </div>
  )
}

export default Sidebar