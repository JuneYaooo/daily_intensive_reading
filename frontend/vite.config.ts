import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  server: {
    host: '0.0.0.0',
    port: 5300,
    proxy: {
      '/api': {
        target: 'http://121.5.254.174:45000',
        changeOrigin: true,
        secure: false
      }
    }
  },
});
