<template>
  <table border="1" cellspacing="0" cellpadding="5">
    <thead>
      <tr>
        <th v-for="(col, index) in columns" :key="index">
          {{ col.label }}
        </th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(item, rowIndex) in data" :key="rowIndex">
      <td
       v-for="(col, colIndex) in columns"
        :key="colIndex"
        :class="{ numeric: isNumber(item[col.key]) && col.key !== 'typeID' }"
      >
        <template v-if="col.key === 'typeID'">
          {{ item[col.key] }}
        </template>
        <template v-else>
          <span v-if="isNumber(item[col.key])">{{ formatNumber(item[col.key]) }}</span>
          <span v-else>{{ item[col.key] }}</span>
        </template>
      </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
export default {
  name: "MarketDataView",
  props: {
    // 传入的数据为数组，每个元素为一个对象
    data: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      // 预定义显示的列和顺序
      columns: [
        { key: "typeID", label: "Type ID" },
        { key: "name", label: "Name" },
        { key: "build_cost", label: "Build Cost" },
        { key: "home_7d_capacity", label: "Home 7d Capacity" },
        { key: "home_7d_movement", label: "Home 7d Movement" },
        { key: "home_buy_price", label: "Home Buy Price" },
        { key: "home_sell_price", label: "Home Sell Price" },
        { key: "jita_7d_capacity", label: "Jita 7d Capacity" },
        { key: "jita_7d_movement", label: "Jita 7d Movement" },
        { key: "jita_buy_price", label: "Jita Buy Price" },
        { key: "jita_sell_price", label: "Jita Sell Price" },
        { key: "margin_p", label: "Margin P" }
      ]
    };
  },
  methods: {
    // 判断是否为数字
    isNumber(value) {
      return typeof value === "number";
    },
    // 格式化数字：逗号分隔并保留两位小数
    formatNumber(value) {
      if (value == null || isNaN(value)) return "";
      return Number(value).toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
    }
  }
};
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
}
th {
  background: #f0f0f0;
  padding: 5px;
  text-align: center;
}
td {
  padding: 5px;
  /* 默认右对齐 */
  text-align: right;
}
td:first-child,
th:first-child {
  text-align: left;
}
.numeric {
  text-align: right;
}
</style>
