import tailwindcss from '@tailwindcss/vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';
import { defineConfig } from 'vite';

const backendTarget = process.env.VITE_DEV_PROXY_TARGET || 'http://127.0.0.1:8000';
const backendProxy = {
  '/api': {
    target: backendTarget,
    changeOrigin: true,
  },
  '/storage': {
    target: backendTarget,
    changeOrigin: true,
  },
  '/storage_pointcloud': {
    target: backendTarget,
    changeOrigin: true,
  },
  '/storage_mesh': {
    target: backendTarget,
    changeOrigin: true,
  },
  '/storage_gs': {
    target: backendTarget,
    changeOrigin: true,
  },
};

const crossOriginIsolationHeaders = {
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cross-Origin-Embedder-Policy': 'require-corp',
};

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    headers: crossOriginIsolationHeaders,
    host: '0.0.0.0',
    proxy: backendProxy,
  },
  preview: {
    headers: crossOriginIsolationHeaders,
    host: '0.0.0.0',
    proxy: backendProxy,
  },
});
