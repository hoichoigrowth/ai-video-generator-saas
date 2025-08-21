import axios, { AxiosInstance, AxiosResponse } from 'axios'
import toast from 'react-hot-toast'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class ApiService {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`🔵 ${config.method?.toUpperCase()} ${config.url}`)
        return config
      },
      (error) => {
        console.error('Request error:', error)
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`🟢 ${response.status} ${response.config.url}`)
        return response
      },
      (error) => {
        console.error('Response error:', error)
        
        if (error.response) {
          const message = error.response.data?.detail || error.response.data?.message || 'An error occurred'
          toast.error(message)
        } else if (error.request) {
          toast.error('Network error - please check your connection')
        } else {
          toast.error('An unexpected error occurred')
        }
        
        return Promise.reject(error)
      }
    )
  }

  // Health check
  async healthCheck() {
    const response = await this.client.get('/health')
    return response.data
  }

  async detailedHealthCheck() {
    const response = await this.client.get('/health/detailed')
    return response.data
  }

  // Project endpoints
  async getProjects() {
    const response = await this.client.get('/api/v1/projects')
    return response.data
  }

  async createProject(data: any) {
    const response = await this.client.post('/api/v1/projects', data)
    return response.data
  }

  async getProject(projectId: string) {
    const response = await this.client.get(`/api/v1/projects/${projectId}`)
    return response.data
  }

  async updateProject(projectId: string, data: any) {
    const response = await this.client.put(`/api/v1/projects/${projectId}`, data)
    return response.data
  }

  async deleteProject(projectId: string) {
    const response = await this.client.delete(`/api/v1/projects/${projectId}`)
    return response.data
  }

  // Script upload (simplified for our backend)
  async uploadScript(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await this.client.post(
      `/upload-script/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  }

  // Extract text from uploaded script
  async extractText(projectId: string) {
    const response = await this.client.get(`/extract-text/${projectId}`)
    return response.data
  }

  // Screenplay endpoints
  async getScreenplays(projectId: string) {
    const response = await this.client.get(`/api/v1/projects/${projectId}/screenplays`)
    return response.data
  }

  async generateScreenplay(projectId: string, scriptText: string, agent: string = 'openai') {
    // Call the backend to generate screenplay using LLM
    const response = await this.client.post(`/generate-screenplay/${projectId}`, {
      script_text: scriptText,
      agent: agent
    })
    return response.data
  }

  async updateScreenplay(projectId: string, screenplayId: string, data: any) {
    const response = await this.client.put(
      `/api/v1/projects/${projectId}/screenplays/${screenplayId}`,
      data
    )
    return response.data
  }

  async mergeScreenplays(projectId: string, screenplayIds: string[]) {
    const response = await this.client.post(
      `/api/v1/projects/${projectId}/merge-screenplays`,
      { screenplay_ids: screenplayIds }
    )
    return response.data
  }

  // Shot division endpoints
  async getShotDivisions(projectId: string) {
    const response = await this.client.get(`/api/v1/projects/${projectId}/shot-divisions`)
    return response.data
  }

  async generateShotDivision(projectId: string, screenplayId: string, agent: string = 'openai') {
    const response = await this.client.post(
      `/api/v1/projects/${projectId}/generate-shot-division`,
      {
        screenplay_id: screenplayId,
        agent,
      }
    )
    return response.data
  }

  async getShots(projectId: string, shotDivisionId: string) {
    const response = await this.client.get(
      `/api/v1/projects/${projectId}/shot-divisions/${shotDivisionId}/shots`
    )
    return response.data
  }

  async updateShot(projectId: string, shotDivisionId: string, shotId: string, data: any) {
    const response = await this.client.put(
      `/api/v1/projects/${projectId}/shot-divisions/${shotDivisionId}/shots/${shotId}`,
      data
    )
    return response.data
  }

  // Character endpoints
  async getCharacters(projectId: string) {
    const response = await this.client.get(`/api/v1/projects/${projectId}/characters`)
    return response.data
  }

  async extractCharacters(projectId: string, screenplayId: string) {
    const response = await this.client.post(
      `/api/v1/projects/${projectId}/extract-characters`,
      { screenplay_id: screenplayId }
    )
    return response.data
  }

  async updateCharacter(projectId: string, characterId: string, data: any) {
    const response = await this.client.put(
      `/api/v1/projects/${projectId}/characters/${characterId}`,
      data
    )
    return response.data
  }

  async generateCharacterImage(projectId: string, characterId: string) {
    const response = await this.client.post(
      `/api/v1/projects/${projectId}/characters/${characterId}/generate-image`
    )
    return response.data
  }

  // Scene generation endpoints
  async generateSceneImages(projectId: string, shotDivisionId: string) {
    const response = await this.client.post(
      `/api/v1/projects/${projectId}/shot-divisions/${shotDivisionId}/generate-scenes`
    )
    return response.data
  }

  async getScenes(projectId: string, shotId: string) {
    const response = await this.client.get(`/api/v1/projects/${projectId}/shots/${shotId}/scenes`)
    return response.data
  }

  async updateScenePrompt(projectId: string, sceneId: string, prompt: string) {
    const response = await this.client.put(`/api/v1/projects/${projectId}/scenes/${sceneId}`, {
      prompt,
    })
    return response.data
  }

  async regenerateScene(projectId: string, sceneId: string) {
    const response = await this.client.post(
      `/api/v1/projects/${projectId}/scenes/${sceneId}/regenerate`
    )
    return response.data
  }

  // Video generation endpoints
  async generateVideo(projectId: string) {
    const response = await this.client.post(`/api/v1/projects/${projectId}/generate-video`)
    return response.data
  }

  async getVideoStatus(projectId: string, videoId: string) {
    const response = await this.client.get(`/api/v1/projects/${projectId}/videos/${videoId}`)
    return response.data
  }

  // Production planning
  async getProductionPlan(projectId: string) {
    const response = await this.client.get(`/api/v1/projects/${projectId}/production-plan`)
    return response.data
  }

  async generateProductionPlan(projectId: string) {
    const response = await this.client.post(`/api/v1/projects/${projectId}/generate-production-plan`)
    return response.data
  }

  // Export endpoints
  async exportData(projectId: string, format: 'csv' | 'excel' | 'pdf', dataType: string) {
    const response = await this.client.post(
      `/api/v1/projects/${projectId}/export`,
      {
        format,
        data_type: dataType,
      },
      {
        responseType: 'blob',
      }
    )
    return response.data
  }

  // Approval system
  async getApprovals(projectId: string) {
    const response = await this.client.get(`/api/v1/projects/${projectId}/approvals`)
    return response.data
  }

  async createApprovalRequest(projectId: string, data: any) {
    const response = await this.client.post(`/api/v1/projects/${projectId}/approvals`, data)
    return response.data
  }

  async respondToApproval(approvalId: string, response: 'approve' | 'reject', notes?: string) {
    const result = await this.client.post(`/api/v1/approvals/${approvalId}/respond`, {
      response,
      notes,
    })
    return result.data
  }

  // File operations
  async uploadFile(projectId: string, file: File, fileType: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_type', fileType)
    
    const response = await this.client.post(`/api/v1/projects/${projectId}/files`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async getFiles(projectId: string) {
    const response = await this.client.get(`/api/v1/projects/${projectId}/files`)
    return response.data
  }
}

export const apiService = new ApiService()
export default apiService