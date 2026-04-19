import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return
          }
          if (id.includes('antd') || id.includes('@ant-design')) {
            return 'antd'
          }
          if (id.includes('@ant-design/plots')) {
            return 'ant-plots'
          }
          if (id.includes('recharts')) {
            return 'recharts'
          }
          if (id.includes('react-dom') || id.includes('/react/')) {
            return 'react-vendor'
          }
          return 'vendor'
        },
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.ts',
  },
})
