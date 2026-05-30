import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// TXN_URL / QKD_URL are injected by docker-compose at startup.
// Locally they default to localhost.
const TXN = process.env.TXN_URL ?? 'http://localhost:8000'
const QKD = process.env.QKD_URL ?? 'http://localhost:8001'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api/txn': {
        target: TXN,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api\/txn/, ''),
      },
      '/api/qkd': {
        target: QKD,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api\/qkd/, ''),
      },
    },
  },
})
