import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiService from '../../services/api'
import toast from 'react-hot-toast'
import { useStore } from '../../store'

const ScriptUpload: React.FC = () => {
  const navigate = useNavigate()
  const { setCurrentProject, setScreenplays, resetScreenplays } = useStore()
  const [dragActive, setDragActive] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [projectId, setProjectId] = useState<string | null>(null)
  const [generatingScreenplay, setGeneratingScreenplay] = useState(false)
  const [extractedScript, setExtractedScript] = useState<string | null>(null)
  const [generatedScreenplay, setGeneratedScreenplay] = useState<string | null>(null)
  const [loadingMessage, setLoadingMessage] = useState('')
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)

  // Clear any existing screenplay data when component mounts
  useEffect(() => {
    resetScreenplays()
  }, [])

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      handleFileUpload(file)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      handleFileUpload(file)
    }
  }

  const handleFileUpload = async (file: File) => {
    setUploadedFile(file)
    setUploadStatus('uploading')
    
    try {
      // Upload the script
      const uploadResponse = await apiService.uploadScript(file)
      setProjectId(uploadResponse.project_id)
      
      // Automatically extract text from the script
      try {
        const extractResponse = await apiService.extractText(uploadResponse.project_id)
        setExtractedScript(extractResponse.text_content)
        toast.success('Script uploaded and text extracted successfully!')
      } catch (extractError) {
        console.error('Failed to extract text:', extractError)
        toast.error('Script uploaded but text extraction failed')
      }
      
      setUploadStatus('success')
    } catch (error) {
      setUploadStatus('error')
      toast.error('Failed to upload script')
      console.error(error)
    }
  }

  const handleGenerateScreenplay = async (agent: string) => {
    if (!projectId || !extractedScript) {
      toast.error('Please upload a script first')
      return
    }

    setSelectedAgent(agent)
    setGeneratingScreenplay(true)
    
    // Animated loading messages
    const loadingMessages = [
      `Initializing ${agent} for screenplay generation...`,
      `Analyzing script structure and characters...`,
      `Applying professional screenplay formatting...`,
      `Processing dialogue and scene descriptions...`,
      `Optimizing character development and pacing...`,
      `Finalizing screenplay with industry standards...`,
      `Almost ready! Polishing the final draft...`
    ]
    
    let messageIndex = 0
    setLoadingMessage(loadingMessages[0])
    
    const messageInterval = setInterval(() => {
      messageIndex = (messageIndex + 1) % loadingMessages.length
      setLoadingMessage(loadingMessages[messageIndex])
    }, 2000)
    
    try {
      // Add a minimum delay for better UX
      const [response] = await Promise.all([
        apiService.generateScreenplay(projectId, extractedScript, agent),
        new Promise(resolve => setTimeout(resolve, 8000)) // 8 second minimum
      ])
      
      clearInterval(messageInterval)
      setLoadingMessage('Screenplay generation complete!')
      
      setGeneratedScreenplay(response.screenplay)
      
      // Store in global state
      const project: any = {
        id: projectId,
        name: uploadedFile?.name || 'Untitled Project',
        description: 'AI Video Generation Project',
        status: 'processing',
        current_stage: 'screenplay_generation',
        settings: {
          video_format: 'mp4',
          resolution: '1920x1080',
          aspect_ratio: '16:9',
          target_duration: 300
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        metadata: {
          extractedScript: extractedScript
        }
      }
      setCurrentProject(project)
      
      const screenplay: any = {
        id: response.project_id,
        project_id: projectId,
        title: uploadedFile?.name || 'Untitled',
        content: response.screenplay,
        version: 1,
        agent_name: response.agent_used,
        generated_at: response.generated_at
      }
      setScreenplays([screenplay])
      
      toast.success(`Screenplay generated successfully using ${agent}!`)
      
      // Navigate to Screenplay Review workspace
      setTimeout(() => {
        navigate('/workspace/screenplay-review')
      }, 1500)
      
    } catch (error) {
      clearInterval(messageInterval)
      setLoadingMessage('')
      toast.error('Failed to generate screenplay')
      console.error(error)
    } finally {
      setTimeout(() => {
        setGeneratingScreenplay(false)
        setLoadingMessage('')
        setSelectedAgent(null)
      }, 1500)
    }
  }

  const resetUpload = () => {
    setUploadedFile(null)
    setUploadStatus('idle')
    setProjectId(null)
    setExtractedScript(null)
    setGeneratedScreenplay(null)
    resetScreenplays()
  }

  if (uploadStatus === 'success' && uploadedFile) {
    return (
      <div className="max-w-4xl mx-auto space-y-8 p-6 relative">
        {/* Loading Overlay */}
        {generatingScreenplay && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl p-12 max-w-md mx-4 text-center shadow-2xl">
              <div className="mb-8">
                {/* Animated AI Brain Icon */}
                <div className="relative mx-auto w-24 h-24 mb-6">
                  <div className="absolute inset-0 rounded-full border-4 border-blue-200"></div>
                  <div className="absolute inset-0 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
                  <div className="absolute inset-2 rounded-full border-2 border-blue-300 border-r-transparent animate-spin animation-delay-200"></div>
                  <div className="absolute inset-4 rounded-full border-2 border-blue-400 border-b-transparent animate-spin animation-delay-400"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
              
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                {selectedAgent} is Working
              </h3>
              
              <div className="h-6 mb-6">
                <p className="text-gray-600 animate-pulse transition-all duration-500">
                  {loadingMessage}
                </p>
              </div>
              
              {/* Progress Bar */}
              <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full animate-pulse"></div>
              </div>
              
              <p className="text-sm text-gray-500">
                Please wait while we craft your professional screenplay...
              </p>
            </div>
          </div>
        )}
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Script Uploaded Successfully!</h1>
          <p className="text-lg text-gray-600">
            Your script is ready for AI processing
          </p>
        </div>

        {/* Success Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-2xl font-semibold text-gray-900 mb-2">
            Upload Complete
          </h3>
          <p className="text-gray-600 mb-6">
            {uploadedFile.name} ({(uploadedFile.size / 1024).toFixed(1)} KB)
          </p>
          
          <div className="flex justify-center space-x-4">
            <button
              onClick={resetUpload}
              className="bg-gray-100 hover:bg-gray-200 text-gray-900 font-medium py-2 px-4 rounded-lg transition-colors duration-200"
            >
              Upload Another Script
            </button>
            <button
              onClick={() => handleGenerateScreenplay('GPT-4')}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 disabled:opacity-50"
              disabled={generatingScreenplay}
            >
              {generatingScreenplay ? 'Generating...' : 'Generate Screenplay'}
            </button>
          </div>
        </div>

        {/* Display Extracted Script */}
        {extractedScript && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mt-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Extracted Script</h3>
            <div className="bg-gray-50 rounded-lg p-6 max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm text-gray-700">{extractedScript}</pre>
            </div>
          </div>
        )}

        {/* Display Generated Screenplay */}
        {generatedScreenplay && (
          <div className="bg-white rounded-xl shadow-sm border border-green-200 p-8 mt-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Generated Screenplay</h3>
            <div className="bg-green-50 rounded-lg p-6 max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm text-gray-700">{generatedScreenplay}</pre>
            </div>
          </div>
        )}

        {/* AI Engine Selection */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <div className="text-center mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Choose AI Engine
            </h2>
            <p className="text-gray-600">
              Select which AI model to use for screenplay generation
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <button
              onClick={() => handleGenerateScreenplay('GPT-4')}
              className="p-6 border-2 border-gray-200 rounded-xl hover:border-green-300 hover:bg-green-50 transition-all duration-200 disabled:opacity-50"
              disabled={generatingScreenplay}
            >
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-lg font-bold text-green-600">GPT</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">OpenAI GPT-4</h3>
              <p className="text-sm text-gray-600 mb-4">Creative & detailed storytelling</p>
              <div className="text-xs text-green-600 font-medium">RECOMMENDED</div>
            </button>

            <button
              onClick={() => handleGenerateScreenplay('Claude')}
              className="p-6 border-2 border-gray-200 rounded-xl hover:border-purple-300 hover:bg-purple-50 transition-all duration-200 disabled:opacity-50"
              disabled={generatingScreenplay}
            >
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-lg font-bold text-purple-600">C</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">Anthropic Claude</h3>
              <p className="text-sm text-gray-600 mb-4">Thoughtful & well-structured</p>
              <div className="text-xs text-purple-600 font-medium">PRECISE</div>
            </button>

            <button
              onClick={() => handleGenerateScreenplay('Gemini')}
              className="p-6 border-2 border-gray-200 rounded-xl hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 disabled:opacity-50"
              disabled={generatingScreenplay}
            >
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-lg font-bold text-blue-600">G</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">Google Gemini</h3>
              <p className="text-sm text-gray-600 mb-4">Factual & coherent narrative</p>
              <div className="text-xs text-blue-600 font-medium">BALANCED</div>
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 p-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Your Script</h1>
        <p className="text-lg text-gray-600">
          Drop your script file here to get started with AI video generation
        </p>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        {uploadStatus === 'uploading' ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-6"></div>
            <h3 className="text-xl font-semibold text-blue-900 mb-2">
              Uploading Script...
            </h3>
            <p className="text-blue-700">
              Please wait while we process your file
            </p>
          </div>
        ) : (
          <div
            className={`p-12 border-2 border-dashed rounded-2xl transition-all duration-200 cursor-pointer ${
              dragActive 
                ? 'border-blue-400 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-upload"
              accept=".txt,.pdf,.doc,.docx"
              onChange={handleChange}
              className="hidden"
            />
            
            <div className="text-center">
              <svg className="w-16 h-16 text-gray-400 mx-auto mb-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              
              {dragActive ? (
                <div>
                  <h3 className="text-xl font-semibold text-blue-900 mb-2">
                    Drop your script file here
                  </h3>
                  <p className="text-blue-700">
                    Release to upload
                  </p>
                </div>
              ) : (
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    Drag & drop your script file here
                  </h3>
                  <p className="text-gray-600 mb-6">
                    or click to browse and select a file
                  </p>
                  
                  <label
                    htmlFor="file-upload"
                    className="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg cursor-pointer transition-colors duration-200"
                  >
                    Browse Files
                  </label>
                  
                  <div className="mt-6 flex items-center justify-center space-x-6 text-sm text-gray-500 bg-gray-100 px-4 py-2 rounded-lg mx-auto max-w-md">
                    <span className="font-medium">Supported:</span>
                    <span>TXT</span>
                    <span>•</span>
                    <span>PDF</span>
                    <span>•</span>
                    <span>DOC</span>
                    <span>•</span>
                    <span>DOCX</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ScriptUpload