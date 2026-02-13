export default {
  root: '.',
  publicDir: 'public',
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:5000', changeOrigin: true },
    },
  },
};
