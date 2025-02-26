<template>
  <table border="1" cellspacing="0" cellpadding="5">
    <thead>
      <tr>
        <th>For</th>
        <th>Product ID</th>
        <th>Name</th>
        <th>Build</th>
        <th>Build Cost</th>
        <th>Buy Loc</th>
        <th>Install Cost</th>
        <th>Material Cost</th>
        <th>Require Quantity</th>
        <th>Output Quantity</th>
        <th>Time</th>
        <th>操作</th>
      </tr>
    </thead>
    <tbody>
      <!-- 使用 <ProductRow> 组件渲染顶层产品列表 -->
      <ProductRow
        v-for="(product, index) in productList"
        :key="index"
        :product="product"
        :parentName="''"
        :depth="0"
      />
    </tbody>
  </table>
</template>

<script>
import ProductRow from './ProductRow.vue'

export default {
  name: 'ProductTable',
  components: { ProductRow },
  props: {
    products: {
      type: [Object, Array],
      required: true
    }
  },
  computed: {
    productList() {
      // 若为数组则直接返回；若为对象则用 Object.values() 转为数组
      if (Array.isArray(this.products)) {
        return this.products
      } else if (this.products && typeof this.products === 'object') {
        return Object.values(this.products)
      }
      return []
    }
  }
}
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 10px;
}
th {
  background: #f0f0f0;
}
</style>
