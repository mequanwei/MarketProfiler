<template>
  <ul>
    <!-- 如果 data 是数组 -->
    <template v-if="Array.isArray(data)">
      <li v-for="(item, index) in data" :key="index">
        <TreeView :data="item" />
      </li>
    </template>
    <!-- 如果 data 是对象 -->
    <template v-else-if="isObject(data)">
      <li v-for="(value, key) in data" :key="key">
        <strong>{{ key }}: </strong>
        <!-- 如果 value 不是对象或数组，则直接显示 -->
        <span v-if="!isObject(value) && !Array.isArray(value)">{{ value }}</span>
        <!-- 否则递归调用 -->
        <TreeView v-else :data="value" />
      </li>
    </template>
    <!-- 如果 data 为基本类型 -->
    <template v-else>
      <li>{{ data }}</li>
    </template>
  </ul>
</template>

<script>
export default {
  name: 'TreeView',
  props: {
    data: {
      type: [Object, Array, String, Number, Boolean],
      required: true
    }
  },
  methods: {
    isObject(val) {
      return val && typeof val === 'object' && !Array.isArray(val);
    }
  }
}
</script>

<style scoped>
ul {
  list-style-type: none;
  padding-left: 1em;
  margin: 0;
}
li {
  margin: 0.2em 0;
}
</style>
