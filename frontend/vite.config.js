import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:1212',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:1212',
        ws: true,
      },
    },
  },
})
