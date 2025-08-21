import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export interface Project {
  id: string
  name: string
  description: string
  status: 'created' | 'processing' | 'completed' | 'error'
  current_stage: 'input' | 'screenplay_generation' | 'shot_division' | 'character_design' | 'scene_generation' | 'video_generation' | 'completed'
  settings: {
    video_format: string
    resolution: string
    aspect_ratio: string
    target_duration: number
  }
  created_at: string
  updated_at: string
  metadata?: Record<string, any>
}

export interface Screenplay {
  id: string
  project_id: string
  title: string
  content: string
  version: number
  agent_name: string
  generated_at: string
  metadata?: Record<string, any>
}

export interface Character {
  id: string
  project_id: string
  name: string
  description: string
  age?: number
  gender?: string
  appearance: string
  personality: string
  role: string
  image_url?: string
  metadata?: Record<string, any>
}

export interface Shot {
  id: string
  shot_number: number
  description: string
  camera_angle: string
  duration: number
  dialogue?: string
  action?: string
  characters: string[]
  location?: string
  time_of_day?: string
  metadata?: Record<string, any>
}

export interface Scene {
  id: string
  shot_id: string
  prompt: string
  image_url?: string
  generated_at?: string
  status: 'pending' | 'generating' | 'completed' | 'error'
  metadata?: Record<string, any>
}

interface AppState {
  // Current project
  currentProject: Project | null
  setCurrentProject: (project: Project | null) => void
  
  // Projects list
  projects: Project[]
  setProjects: (projects: Project[]) => void
  addProject: (project: Project) => void
  updateProject: (projectId: string, updates: Partial<Project>) => void
  
  // Screenplays
  screenplays: Screenplay[]
  setScreenplays: (screenplays: Screenplay[]) => void
  addScreenplay: (screenplay: Screenplay) => void
  updateScreenplay: (screenplayId: string, updates: Partial<Screenplay>) => void
  
  // Characters
  characters: Character[]
  setCharacters: (characters: Character[]) => void
  addCharacter: (character: Character) => void
  updateCharacter: (characterId: string, updates: Partial<Character>) => void
  removeCharacter: (characterId: string) => void
  
  // Shots
  shots: Shot[]
  setShots: (shots: Shot[]) => void
  addShot: (shot: Shot) => void
  updateShot: (shotId: string, updates: Partial<Shot>) => void
  removeShot: (shotId: string) => void
  
  // Scenes
  scenes: Scene[]
  setScenes: (scenes: Scene[]) => void
  addScene: (scene: Scene) => void
  updateScene: (sceneId: string, updates: Partial<Scene>) => void
  removeScene: (sceneId: string) => void
  
  // UI State
  currentWorkspace: string
  setCurrentWorkspace: (workspace: string) => void
  
  isLoading: boolean
  setIsLoading: (loading: boolean) => void
  
  error: string | null
  setError: (error: string | null) => void
  
  // WebSocket connection
  isConnected: boolean
  setIsConnected: (connected: boolean) => void
  
  // Reset functions
  resetAll: () => void
  resetScreenplays: () => void
}

export const useStore = create<AppState>()(
  devtools(
    (set, get) => ({
      // Current project
      currentProject: null,
      setCurrentProject: (project) => set({ currentProject: project }),
      
      // Projects
      projects: [],
      setProjects: (projects) => set({ projects }),
      addProject: (project) => set((state) => ({ projects: [...state.projects, project] })),
      updateProject: (projectId, updates) =>
        set((state) => ({
          projects: state.projects.map((p) =>
            p.id === projectId ? { ...p, ...updates } : p
          ),
          currentProject:
            state.currentProject?.id === projectId
              ? { ...state.currentProject, ...updates }
              : state.currentProject,
        })),
      
      // Screenplays
      screenplays: [],
      setScreenplays: (screenplays) => set({ screenplays }),
      addScreenplay: (screenplay) =>
        set((state) => ({ screenplays: [...state.screenplays, screenplay] })),
      updateScreenplay: (screenplayId, updates) =>
        set((state) => ({
          screenplays: state.screenplays.map((s) =>
            s.id === screenplayId ? { ...s, ...updates } : s
          ),
        })),
      
      // Characters
      characters: [],
      setCharacters: (characters) => set({ characters }),
      addCharacter: (character) =>
        set((state) => ({ characters: [...state.characters, character] })),
      updateCharacter: (characterId, updates) =>
        set((state) => ({
          characters: state.characters.map((c) =>
            c.id === characterId ? { ...c, ...updates } : c
          ),
        })),
      removeCharacter: (characterId) =>
        set((state) => ({
          characters: state.characters.filter((c) => c.id !== characterId),
        })),
      
      // Shots
      shots: [],
      setShots: (shots) => set({ shots }),
      addShot: (shot) => set((state) => ({ shots: [...state.shots, shot] })),
      updateShot: (shotId, updates) =>
        set((state) => ({
          shots: state.shots.map((s) => (s.id === shotId ? { ...s, ...updates } : s)),
        })),
      removeShot: (shotId) =>
        set((state) => ({
          shots: state.shots.filter((s) => s.id !== shotId),
        })),
      
      // Scenes
      scenes: [],
      setScenes: (scenes) => set({ scenes }),
      addScene: (scene) => set((state) => ({ scenes: [...state.scenes, scene] })),
      updateScene: (sceneId, updates) =>
        set((state) => ({
          scenes: state.scenes.map((s) => (s.id === sceneId ? { ...s, ...updates } : s)),
        })),
      removeScene: (sceneId) =>
        set((state) => ({
          scenes: state.scenes.filter((s) => s.id !== sceneId),
        })),
      
      // UI State
      currentWorkspace: 'dashboard',
      setCurrentWorkspace: (workspace) => set({ currentWorkspace: workspace }),
      
      isLoading: false,
      setIsLoading: (loading) => set({ isLoading: loading }),
      
      error: null,
      setError: (error) => set({ error }),
      
      // WebSocket
      isConnected: false,
      setIsConnected: (connected) => set({ isConnected: connected }),
      
      // Reset functions
      resetAll: () => set({
        currentProject: null,
        projects: [],
        screenplays: [],
        characters: [],
        shots: [],
        scenes: [],
        isLoading: false,
        error: null
      }),
      
      resetScreenplays: () => set({
        screenplays: []
      }),
    }),
    {
      name: 'ai-video-generator-store',
    }
  )
)