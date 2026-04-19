import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

function getPackageChunkName(id: string): string | undefined {
  if (!id.includes('node_modules')) {
    return undefined
  }

  const afterNodeModules = id.split('node_modules/')[1]
  if (!afterNodeModules) {
    return 'vendor'
  }

  const segments = afterNodeModules.split('/')
  const packageName = segments[0]?.startsWith('@') ? `${segments[0]}/${segments[1]}` : segments[0]

  if (!packageName) {
    return 'vendor'
  }

  if (packageName === 'react' || packageName === 'react-dom' || packageName === 'react-router-dom') {
    return 'react-vendor'
  }

  if (packageName === 'antd' || packageName === '@ant-design/icons' || packageName === '@ant-design/cssinjs') {
    return 'antd'
  }

  if (packageName === '@ant-design/plots') {
    return 'ant-plots'
  }

  if (packageName === 'recharts') {
    return 'recharts'
  }

  if (packageName === 'html2canvas' || packageName === 'jspdf') {
    return 'reporting'
  }

  if (packageName === 'axios' || packageName === 'zustand') {
    return 'app-vendor'
  }

  return `vendor-${packageName.replace('@', '').replace('/', '-')}`
}

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      output: {
        manualChunks(id) {
          return getPackageChunkName(id)
        },
      },
    },
  },
})
