import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'

// Las variables sin prefijo VITE_ (BACKEND_URL, FRONTEND_PORT…) solo existen aquí, nunca llegan al navegador.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendUrl = env.BACKEND_URL || 'http://127.0.0.1:8000'
  const allowedHosts = (env.FRONTEND_ALLOWED_HOSTS || '').split(',').map((host) => host.trim()).filter(Boolean)

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    server: {
      port: Number(env.FRONTEND_PORT || 5173),
      strictPort: true,
      allowedHosts,
      // /api, /media y /static van al backend: mismo origen para el navegador (sin CORS y con la
      // cookie del refresh token en SameSite=Strict).
      proxy: {
        '/api': backendUrl,
        '/media': backendUrl,
        '/static': backendUrl,
      },
    },
  }
})
