const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      '/backend': {
        target: 'http://web:5000',
        changeOrigin: true,
        pathRewrite: {
          '^/backend': ''
        }
      }
    }
  }
})
