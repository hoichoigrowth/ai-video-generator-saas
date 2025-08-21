import React from 'react'
import { ChartBarIcon, DocumentChartBarIcon, CalendarIcon, UserGroupIcon } from '@heroicons/react/24/outline'

const ProductionDesign: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Production Design Hub</h1>
        <p className="text-gray-600 mt-1">
          Comprehensive production planning and design management
        </p>
      </div>
      
      <div className="workspace-card p-12 text-center">
        <ChartBarIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Production Design Hub
        </h3>
        <p className="text-gray-600">
          This workspace will contain production planning tools, resource management, and design coordination features.
        </p>
      </div>
    </div>
  )
}

export default ProductionDesign