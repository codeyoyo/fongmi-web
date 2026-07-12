<template>
  <div class="placeholder">
    <n-card :title="title">
      <n-empty description="功能开发中..." />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { NCard, NEmpty } from 'naive-ui'

const route = useRoute()
const title = computed(() => (route.meta?.title as string) || '页面')
</script>

<style scoped>
.placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 24px;
  box-sizing: border-box;
}
</style>
