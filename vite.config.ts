import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
export default defineConfig({plugins:[vue()],server:{port:5173,strictPort:false},build:{chunkSizeWarningLimit:900,rollupOptions:{output:{manualChunks:{three:['three']}}}}});
