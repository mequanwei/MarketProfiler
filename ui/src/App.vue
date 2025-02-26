<template>
  <div id="app">
    <h1>Market JSON</h1>
    <div style="margin-bottom: 1em;">
      <input v-model="name" placeholder="name" />
      <button @click="fetchProductTree">B.O.M</button>
      <button @click="fetchMarketProfile">MarketData</button>
    </div>
    <div v-if="result">
      <h2>Result</h2>
      <ProductTable :products="result" />
    </div>
  </div>
</template>

<script>
import ProductTable from './components/ProductTable.vue';

export default {
  name: 'App',
  components: { ProductTable },
  data() {
    return {
      name: '',
      result: null
    }
  },
  methods: {
    async fetchProductTree() {
      // 注意替换 URL 中的 xxx 为输入的值，使用 encodeURIComponent 进行编码
      try {
        const response = await fetch(`/backend/industrial/get_product_tree/?name=${encodeURIComponent(this.name)}`);
        if (!response.ok) throw new Error('请求失败');
        this.result = await response.json();
      } catch (error) {
        console.error(error);
        alert('获取产品树数据失败，请检查后端服务');
      }
    },
    async fetchMarketProfile() {
      try {
        const response = await fetch(`/backend/industrial/marketprofile/`);
        if (!response.ok) throw new Error('请求失败');
        this.result = await response.json();
      } catch (error) {
        console.error(error);
        alert('获取市场数据失败，请检查后端服务');
      }
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  margin: 2em;
}
input {
  padding: 0.5em;
  font-size: 1em;
}
button {
  margin-left: 0.5em;
  padding: 0.5em 1em;
  font-size: 1em;
}
</style>
