import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/query': {
        target: 'http://127.0.0.1:7860',
        changeOrigin: true
      },
      '/embed': {
        target: 'http://127.0.0.1:7860',
        changeOrigin: true
      },
      '/health': {
        target: 'http://127.0.0.1:7860',
        changeOrigin: true
      },
      '/upload': {
        target: 'http://127.0.0.1:7860',
        changeOrigin: true
      },
      '/documents': {
        target: 'http://127.0.0.1:7860',
        changeOrigin: true
      }
    }
  }
});
