<template>
  <div ref="el" style="width:100%;height:300px"></div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{ option: any }>()
const el = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const render = () => {
  if (!el.value || !props.option) return
  if (!chart) chart = echarts.init(el.value)
  chart.setOption(props.option, true)
}
onMounted(() => {
  render()
  window.addEventListener('resize', resize)
})
watch(() => props.option, render, { deep: true })
const resize = () => chart?.resize()
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
})
</script>
