<template>
  <div
    style="width: 100%; height: 100vh;"
    v-loading="loading"
    element-loading-text="正在生成 LDA 可视化，请稍候..."
  >
    <iframe
      v-if="ldaHtmlUrl"
      ref="iframeRef"
      :src="ldaHtmlUrl"
      @load="onIframeLoad"
      style="width:100%; height:100%; border:none;">
    </iframe>
  </div>
  
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const ldaHtmlUrl = ref('')
const loading = ref(true)
const iframeRef = ref<HTMLIFrameElement | null>(null)

const onIframeLoad = () => {
  loading.value = false
}

onMounted(async () => {
  try {
    loading.value = true
    const res = await fetch('http://127.0.0.1:5000/lda')
    const htmlText = await res.text()
    const blob = new Blob([htmlText], { type: 'text/html' })
    ldaHtmlUrl.value = URL.createObjectURL(blob)
    // 若浏览器未触发 load（极少数情况），兜底关闭 loading
    setTimeout(() => {
      if (loading.value) loading.value = false
    }, 8000)
  } catch (e) {
    loading.value = false
    console.error('加载 LDA 可视化失败:', e)
  }
})
</script>

<style scoped>
/* 可自定义 iframe 样式 */
</style>
