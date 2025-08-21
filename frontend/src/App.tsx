import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from '@/components/layout/Layout'
import Dashboard from '@/pages/Dashboard'
import ScriptUpload from '@/pages/workspaces/ScriptUpload'
import ScreenplayReview from '@/pages/workspaces/ScreenplayReview'
import ShotBreakdown from '@/pages/workspaces/ShotBreakdown'
import ProductionDesign from '@/pages/workspaces/ProductionDesign'
import CharacterRoster from '@/pages/workspaces/CharacterRoster'
import CharacterGallery from '@/pages/workspaces/CharacterGallery'
import ScenePromptEditor from '@/pages/workspaces/ScenePromptEditor'
import SceneImageSelector from '@/pages/workspaces/SceneImageSelector'
import VideoGeneration from '@/pages/workspaces/VideoGeneration'
import ProjectSettings from '@/pages/ProjectSettings'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/workspace/script-upload" element={<ScriptUpload />} />
          <Route path="/workspace/screenplay-review" element={<ScreenplayReview />} />
          <Route path="/workspace/shot-breakdown" element={<ShotBreakdown />} />
          <Route path="/workspace/production-design" element={<ProductionDesign />} />
          <Route path="/workspace/character-roster" element={<CharacterRoster />} />
          <Route path="/workspace/character-gallery" element={<CharacterGallery />} />
          <Route path="/workspace/scene-prompt-editor" element={<ScenePromptEditor />} />
          <Route path="/workspace/scene-image-selector" element={<SceneImageSelector />} />
          <Route path="/workspace/video-generation" element={<VideoGeneration />} />
          <Route path="/project/settings" element={<ProjectSettings />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App