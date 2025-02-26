<template>
  <!-- 当前产品的行，绑定背景颜色 -->
  <tr :style="{ backgroundColor: backgroundColor }">
    <!-- “For” 列，顶层为空，子层显示父级名称 -->
    <td>{{ parentName || '' }}</td>
    <td>{{ product.product_id }}</td>
    <td>
      <!-- 给“Name”列做缩进 -->
      <div :style="{ marginLeft: `${depth * 20}px` }">
        <!-- 若有子层，名称可点击展开/收起 -->
        <span
          v-if="hasChildren"
          @click="toggleExpand"
          style="cursor: pointer; color: blue;"
        >
          {{ product.name }}
        </span>
        <span v-else>{{ product.name }}</span>
      </div>
    </td>
    <td class="mid">{{ product.build }}</td>
    <td class="numeric">{{ formatNumber(product.build_cost) }}</td>
    <td class="mid">{{ product.buy_loc }}</td>
    <td class="numeric">{{ formatNumber(product.install_cost) }}</td>
    <td class="numeric">{{ formatNumber(product.material_cost) }}</td>
    <td class="numeric">{{  product.require_quantity != null ? formatNumber(product.require_quantity) : '0' }}</td>
    <td class="numeric">{{ formatNumber(product.output_quantity) }}</td>
    <td class="numeric">{{ formatNumber(product.time) }}</td>
    <td>
      <!-- 若有子层，显示“展开/收起”按钮 -->
      <button v-if="hasChildren" @click="toggleExpand">
        {{ expanded ? '收起' : '展开' }}
      </button>
    </td>
  </tr>

  <!-- 如果有子层且已展开，则在同一个 <tbody> 中递归渲染子行 -->
  <template v-if="expanded && hasChildren">
    <ProductRow
      v-for="(child, index) in product.inputs"
      :key="index"
      :product="child"
      :parentName="product.name"
      :depth="depth + 1"
    />
  </template>
</template>

<script>
export default {
  name: 'ProductRow',
  props: {
    product: { type: Object, required: true },
    // 父级产品的名称，用于“For”列显示
    parentName: { type: String, default: '' },
    // 当前层级深度，控制缩进和背景颜色
    depth: { type: Number, default: 0 }
  },
  data() {
    return {
      expanded: false
    }
  },
  computed: {
    hasChildren() {
      return Array.isArray(this.product.inputs) && this.product.inputs.length > 0
    },
    // 根据层级返回不同的背景色（蓝色调）
    backgroundColor() {
      const colors = ['#e6f7ff', '#bae7ff', '#91d5ff', '#69c0ff', '#40a9ff'];
      return colors[this.depth % colors.length];
    }
  },
  methods: {
    toggleExpand() {
      this.expanded = !this.expanded
    },
    // 格式化数字：逗号分隔并保留两位小数
    formatNumber(value) {
      if (value == null || isNaN(value)) return ''
      return Number(value).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }
  },
  // 递归组件需要在自身注册
  components: {
    ProductRow: () => import('./ProductRow.vue')
  }
}
</script>

<style scoped>
/* 可根据需要进一步美化样式 */
.numeric {
  text-align: right;
}
.mid {
  text-align: center;
}
</style>
