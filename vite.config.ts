import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    proxy: {
      '/api': { target: process.env.VITE_DEV_API_PROXY ?? 'http://127.0.0.1:8000', changeOrigin: true },
      '/media': { target: process.env.VITE_DEV_API_PROXY ?? 'http://127.0.0.1:8000', changeOrigin: true },
      '/admin': { target: process.env.VITE_DEV_API_PROXY ?? 'http://127.0.0.1:8000', changeOrigin: true },
      '/static': { target: process.env.VITE_DEV_API_PROXY ?? 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
})
