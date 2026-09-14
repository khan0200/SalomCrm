<script setup lang="ts">
defineProps<{
  x: number
  y: number
  width: number
  height: number
}>()
</script>

<template>
  <div
    class="canvas-marquee-select pointer-events-none absolute z-[9999]"
    :style="{
      left: `${x}px`,
      top: `${y}px`,
      width: `${width}px`,
      height: `${height}px`,
    }"
  />
</template>

<style scoped>
.canvas-marquee-select {
  border: 1.5px dashed #2563eb;
  background: rgba(37, 99, 235, 0.07);
  border-radius: 2px;
  box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.12);
}
</style>
