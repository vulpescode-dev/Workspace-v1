/** Variables del frontend (frontend/.env). Un solo lugar para leerlas; el resto del código importa `env`. */
export const env = {
  projectName: import.meta.env.VITE_PROJECT_NAME || 'Workspace',
  projectCode: (import.meta.env.VITE_PROJECT_CODE || 'ws').toLowerCase(),
  apiUrl: (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, ''),
} as const
