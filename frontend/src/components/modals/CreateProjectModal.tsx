import React from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { Fragment } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import apiService from '@/services/api'
import { useStore } from '@/store'
import toast from 'react-hot-toast'

interface CreateProjectModalProps {
  isOpen: boolean
  onClose: () => void
}

interface ProjectFormData {
  name: string
  description: string
  video_format: string
  resolution: string
  aspect_ratio: string
  target_duration: number
}

const CreateProjectModal: React.FC<CreateProjectModalProps> = ({ isOpen, onClose }) => {
  const queryClient = useQueryClient()
  const { addProject, setCurrentProject } = useStore()
  
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProjectFormData>({
    defaultValues: {
      video_format: 'mp4',
      resolution: '1080p',
      aspect_ratio: '9:16',
      target_duration: 60,
    },
  })

  const createProjectMutation = useMutation({
    mutationFn: apiService.createProject,
    onSuccess: (data) => {
      addProject(data)
      setCurrentProject(data)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Project created successfully!')
      reset()
      onClose()
    },
  })

  const onSubmit = (data: ProjectFormData) => {
    createProjectMutation.mutate({
      name: data.name,
      description: data.description,
      settings: {
        video_format: data.video_format,
        resolution: data.resolution,
        aspect_ratio: data.aspect_ratio,
        target_duration: data.target_duration,
      },
    })
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between mb-6">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-semibold leading-6 text-gray-900"
                  >
                    Create New Project
                  </Dialog.Title>
                  <button
                    onClick={handleClose}
                    className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                  {/* Project Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Project Name
                    </label>
                    <input
                      type="text"
                      {...register('name', { required: 'Project name is required' })}
                      className="input-field"
                      placeholder="Enter project name"
                    />
                    {errors.name && (
                      <p className="text-red-500 text-xs mt-1">{errors.name.message}</p>
                    )}
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <textarea
                      {...register('description')}
                      rows={3}
                      className="textarea-field"
                      placeholder="Describe your project..."
                    />
                  </div>

                  {/* Video Settings */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Video Format
                      </label>
                      <select
                        {...register('video_format')}
                        className="input-field"
                      >
                        <option value="mp4">MP4</option>
                        <option value="mov">MOV</option>
                        <option value="avi">AVI</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Resolution
                      </label>
                      <select
                        {...register('resolution')}
                        className="input-field"
                      >
                        <option value="720p">720p</option>
                        <option value="1080p">1080p</option>
                        <option value="4k">4K</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Aspect Ratio
                      </label>
                      <select
                        {...register('aspect_ratio')}
                        className="input-field"
                      >
                        <option value="16:9">16:9 (Landscape)</option>
                        <option value="9:16">9:16 (Portrait)</option>
                        <option value="1:1">1:1 (Square)</option>
                        <option value="4:3">4:3 (Standard)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Duration (seconds)
                      </label>
                      <input
                        type="number"
                        {...register('target_duration', { 
                          required: 'Duration is required',
                          min: { value: 15, message: 'Minimum 15 seconds' },
                          max: { value: 300, message: 'Maximum 300 seconds' }
                        })}
                        className="input-field"
                        placeholder="60"
                      />
                      {errors.target_duration && (
                        <p className="text-red-500 text-xs mt-1">{errors.target_duration.message}</p>
                      )}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={handleClose}
                      className="flex-1 btn-secondary"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={createProjectMutation.isPending}
                      className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {createProjectMutation.isPending ? 'Creating...' : 'Create Project'}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}

export default CreateProjectModal