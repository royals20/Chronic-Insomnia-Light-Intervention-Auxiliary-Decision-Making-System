import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000';

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': '/src',
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
    build: {
      chunkSizeWarningLimit: 900,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) {
              return undefined;
            }
            if (id.includes('element-plus')) {
              return 'element-plus';
            }
            if (id.includes('echarts')) {
              return 'echarts';
            }
            if (id.includes('vue-router') || id.includes('pinia') || id.includes('/vue/')) {
              return 'vue-core';
            }
            if (id.includes('axios')) {
              return 'network';
            }
            return 'vendor';
          },
        },
      },
    },
  };
});
