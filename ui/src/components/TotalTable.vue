<template>
  <div v-if="totalData">
    <table class="total-table">
      <thead>
        <tr>
          <th>
          <button @click="copyData(totalData)">复制</button></th>
          <th>名称</th>
          <th>数量</th>
          <th>单价</th>
          <th>Total Cost</th>
        </tr>
      </thead>
      <tbody>
        <!-- 遍历 totalData 对象的每个键 -->
        <tr v-for="(value, name) in totalData" :key="name">
          <td> {{name}}</td>
          <td>{{ name }}</td>
          <td class="numeric">{{ formatValue(value.total_quantity) }}</td>
          <td class="numeric">{{ formatValue(value.total_cost / value.total_quantity) }}</td>
          <td class="numeric">{{ formatValue(value.total_cost) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div v-else>
    <p>暂无汇总数据</p>
  </div>
</template>

<script>
export default {
  name: "TotalTable",
  props: {
    // 传入的 result 对象
    result: {
      type: Object,
      required: true
    }
  },
  computed: {
    // 从 result 中提取 total 数据
    totalData() {
      if (!this.result) return null;
      const keys = Object.keys(this.result);
      // 假设只有一个产品键，如 "product_33468"，并且其内部有 total 字段
      if (keys.length > 0 && this.result[keys[0]].total) {
        return this.result[keys[0]].total;
      }
      return null;
    }
  },
  methods: {
    // 格式化数值：如果是数字则逗号分隔并保留两位小数，否则返回 '-' 或原值
    formatValue(value,bit) {
      if (value === undefined || value === null) {
        return "-";
      }

      if (typeof value === "number") {
        return Number(value).toLocaleString("en-US", {
          minimumFractionDigits: bit,
          maximumFractionDigits: 2
        });
      }
      return value;
    },
    copyData(result) {
      // 处理 result，确保它是数组
      console.info(result)
      // 格式化文本，将 item 和 qty 拼接
      const dataArray = Object.entries(result).map(([key, value]) => ({
        item: key,
        total_quantity: value.total_quantity
      }));
      const text = dataArray.map(row => `${row.item}  ${row.total_quantity}`).join("\n");
      
      
      // 复制到剪贴板
      
      const textarea = document.createElement("textarea");
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
  }
};
</script>

<style scoped>
.total-table {
  width: auto;
  max-width: 600px;
  margin: 10px auto;
  border-collapse: collapse;
}

.total-table th,
.total-table td {
  border: 1px solid #ccc;
  padding: 4px 8px;
  text-align: right;
}

.total-table th:first-child,
.total-table td:first-child {
  text-align: left;
}

.numeric {
  text-align: right;
}
</style>
