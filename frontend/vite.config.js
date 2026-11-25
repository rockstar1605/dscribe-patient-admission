import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // The backend's CORS settings expect this exact port.
  server: { port: 5173, strictPort: true },
})
