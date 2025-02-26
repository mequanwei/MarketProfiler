const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      '/backend': {
        target: 'http://10.1.9.74:5000',
        changeOrigin: true,
        pathRewrite: {
          '^/backend': ''
        }
      }
    }
  }
})
