<template>
  <div id="app">
    <h1>Market JSON</h1>
    <div style="margin-bottom: 1em;">
      <input v-model="name" placeholder="name" />
      <button @click="fetchProductTree">B.O.M</button>
      <button @click="fetchMarketProfile">MarketData</button>
      <button @click="updateData">Update Data</button>
      <button @click="updateBuildCost">Update Build Cost</button>
    </div>
    <div v-if="result">
      <h2>Result</h2>
      <!-- 根据 currentView 显示不同的组件 -->
      <ProductTable v-if="currentView === 'BOM'" :products="result" />
      <MarketDataView v-if="currentView === 'MarketData'" :data="result" />
    </div>
    <div v-if="showUpdateSuccess && currentView === 'UpdateData'" >
      更新成功！
    </div>
  </div>
</template>

<script>
import ProductTable from './components/ProductTable.vue';
import MarketDataView from './components/MarketDataView.vue';

export default {
  name: 'App',
  components: { ProductTable,MarketDataView },
  data() {
    return {
      name: '',
      result: null,
      currentView :'',
      showUpdateSuccess: false
    }
  },
  methods: {
    async fetchProductTree() {
      // 注意替换 URL 中的 xxx 为输入的值，使用 encodeURIComponent 进行编码
      try {
        const response = await fetch(`/backend/industrial/get_product_tree/?name=${encodeURIComponent(this.name)}`);
        if (!response.ok) throw new Error('请求失败');
        this.result = await response.json();
        this.currentView = 'BOM';
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
        this.currentView = 'MarketData';
      } catch (error) {
        console.error(error);
        alert('获取市场数据失败，请检查后端服务');
      }
    }, 
    async updateData() {
      try {
        const response = await fetch(`/backend/industrial/update_all_network_data/`);
        if (!response.ok) throw new Error('请求失败');
        this.result = null;
        this.showUpdateSuccess = true;
        this.currentView = 'UpdateData';
      } catch (error) {
        console.error(error);
        alert('更新市场数据失败，请检查后端服务');
      }
    },
    async updateBuildCost() {
      try {
        const response = await fetch(`/backend/industrial/updatebuildcost/`);
        if (!response.ok) throw new Error('请求失败');
        this.result = null;
        this.showUpdateSuccess = true;
        this.currentView = 'UpdateData';
      } catch (error) {
        console.error(error);
        alert('更新数据失败，请检查后端服务');
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
.success-message {
  margin-top: 1em;
  padding: 1em;
  background-color: #e0ffe0;
  border: 1px solid #00aa00;
  text-align: center;
  font-size: 1.2em;
  color: #007700;
}
</style>
