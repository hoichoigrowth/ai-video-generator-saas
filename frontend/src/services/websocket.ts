import io, { Socket } from 'socket.io-client'
import toast from 'react-hot-toast'
import { useStore } from '@/store'

class WebSocketService {
  private socket: Socket | null = null
  private projectId: string | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  connect(projectId: string) {
    if (this.socket && this.projectId === projectId) {
      return
    }

    this.disconnect()
    this.projectId = projectId

    const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

    this.socket = io(WS_URL, {
      transports: ['websocket'],
      upgrade: true,
    })

    this.setupEventListeners()
    this.joinProject(projectId)
  }

  private setupEventListeners() {
    if (!this.socket) return

    this.socket.on('connect', () => {
      console.log('🔗 WebSocket connected')
      useStore.getState().setIsConnected(true)
      this.reconnectAttempts = 0
      
      if (this.projectId) {
        this.joinProject(this.projectId)
      }
    })

    this.socket.on('disconnect', (reason) => {
      console.log('🔌 WebSocket disconnected:', reason)
      useStore.getState().setIsConnected(false)
      
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, don't reconnect automatically
        return
      }
      
      // Auto-reconnect for client-side disconnects
      this.handleReconnect()
    })

    this.socket.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error)
      useStore.getState().setIsConnected(false)
      this.handleReconnect()
    })

    // Project update events
    this.socket.on('project_updated', (data) => {
      console.log('📡 Project updated:', data)
      const { updateProject } = useStore.getState()
      updateProject(data.project_id, data.updates)
      
      toast.success(`Project updated: ${data.message || 'Status changed'}`)
    })

    // Screenplay generation events
    this.socket.on('screenplay_generated', (data) => {
      console.log('📝 Screenplay generated:', data)
      const { addScreenplay, updateProject } = useStore.getState()
      
      if (data.screenplay) {
        addScreenplay(data.screenplay)
      }
      
      if (data.project_updates) {
        updateProject(data.project_id, data.project_updates)
      }
      
      toast.success('Screenplay generation completed!')
    })

    // Shot division events
    this.socket.on('shot_division_completed', (data) => {
      console.log('🎬 Shot division completed:', data)
      const { setShots, updateProject } = useStore.getState()
      
      if (data.shots) {
        setShots(data.shots)
      }
      
      if (data.project_updates) {
        updateProject(data.project_id, data.project_updates)
      }
      
      toast.success('Shot division completed!')
    })

    // Character extraction events
    this.socket.on('characters_extracted', (data) => {
      console.log('👥 Characters extracted:', data)
      const { setCharacters, updateProject } = useStore.getState()
      
      if (data.characters) {
        setCharacters(data.characters)
      }
      
      if (data.project_updates) {
        updateProject(data.project_id, data.project_updates)
      }
      
      toast.success('Character extraction completed!')
    })

    // Scene generation events
    this.socket.on('scene_generated', (data) => {
      console.log('🖼️ Scene generated:', data)
      const { updateScene } = useStore.getState()
      
      if (data.scene) {
        updateScene(data.scene.id, data.scene)
      }
      
      toast.success(`Scene generated for shot ${data.shot_number}`)
    })

    this.socket.on('scene_generation_progress', (data) => {
      console.log('⏳ Scene generation progress:', data)
      toast.loading(`Generating scenes: ${data.completed}/${data.total}`, {
        id: 'scene-generation',
      })
      
      if (data.completed === data.total) {
        toast.dismiss('scene-generation')
        toast.success('All scenes generated!')
      }
    })

    // Video generation events
    this.socket.on('video_generation_started', (data) => {
      console.log('🎥 Video generation started:', data)
      const { updateProject } = useStore.getState()
      
      updateProject(data.project_id, {
        current_stage: 'video_generation',
        status: 'processing',
      })
      
      toast.loading('Video generation started...', { id: 'video-generation' })
    })

    this.socket.on('video_generation_progress', (data) => {
      console.log('⏳ Video generation progress:', data)
      toast.loading(`Generating video: ${data.progress}%`, {
        id: 'video-generation',
      })
    })

    this.socket.on('video_generation_completed', (data) => {
      console.log('🎬 Video generation completed:', data)
      const { updateProject } = useStore.getState()
      
      updateProject(data.project_id, {
        current_stage: 'completed',
        status: 'completed',
      })
      
      toast.dismiss('video-generation')
      toast.success('Video generation completed! 🎉')
    })

    // Error events
    this.socket.on('error', (data) => {
      console.error('❌ WebSocket error:', data)
      const { setError } = useStore.getState()
      setError(data.message || 'An error occurred')
      toast.error(data.message || 'An error occurred')
    })

    // Approval events
    this.socket.on('approval_request', (data) => {
      console.log('✋ Approval request:', data)
      toast('Approval required for next step', {
        icon: '✋',
        duration: 6000,
      })
    })

    this.socket.on('approval_responded', (data) => {
      console.log('✅ Approval responded:', data)
      const message = data.response === 'approve' ? 'Approved! Continuing workflow...' : 'Rejected. Workflow paused.'
      toast(message, {
        icon: data.response === 'approve' ? '✅' : '❌',
      })
    })

    // Task status events
    this.socket.on('task_started', (data) => {
      console.log('🚀 Task started:', data)
      toast.loading(data.message || 'Task started...', {
        id: data.task_id,
      })
    })

    this.socket.on('task_completed', (data) => {
      console.log('✅ Task completed:', data)
      toast.dismiss(data.task_id)
      toast.success(data.message || 'Task completed!')
    })

    this.socket.on('task_failed', (data) => {
      console.log('❌ Task failed:', data)
      toast.dismiss(data.task_id)
      toast.error(data.message || 'Task failed')
    })
  }

  private joinProject(projectId: string) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('join_project', { project_id: projectId })
      console.log(`🏠 Joined project: ${projectId}`)
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('❌ Max reconnection attempts reached')
      toast.error('Connection lost. Please refresh the page.')
      return
    }

    this.reconnectAttempts++
    const delay = Math.pow(2, this.reconnectAttempts) * 1000 // Exponential backoff

    console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
    
    setTimeout(() => {
      if (this.socket && this.projectId) {
        this.socket.connect()
      }
    }, delay)
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.projectId = null
    this.reconnectAttempts = 0
    useStore.getState().setIsConnected(false)
  }

  // Emit custom events
  emit(event: string, data: any) {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data)
    } else {
      console.warn('Socket not connected, cannot emit event:', event)
    }
  }

  // Check if connected
  isConnected(): boolean {
    return this.socket?.connected || false
  }
}

export const websocketService = new WebSocketService()
export default websocketService