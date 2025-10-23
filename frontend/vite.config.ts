import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load env file from parent directory
  const env = loadEnv(mode, '../', '')
  
  return {
    plugins: [react()],
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    // Make environment variables available to the app
    define: {
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(env.VITE_API_BASE_URL || 'http://localhost:8000')
    }
  }
})
