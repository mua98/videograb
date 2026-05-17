<script setup>
import { ref } from 'vue'
import { parseVideo, buildDownloadUrl } from '../services/api'

const videoUrl = ref('')
const loading = ref(false)
const result = ref(null)
const error = ref('')

const handleParse = async () => {
  if (!videoUrl.value.trim()) {
    error.value = '请输入视频链接'
    return
  }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    const response = await parseVideo(videoUrl.value)
    if (response.data.success) {
      result.value = response.data.data
    } else {
      error.value = response.data.error || '解析失败'
    }
  } catch (err) {
    error.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

const handleDownload = () => {
  if (!result.value?.video_url) return
  const url = buildDownloadUrl(result.value.video_url)
  window.open(url, '_blank')
}
</script>

<template>
  <div class="max-w-2xl mx-auto p-6">
    <!-- 标题 -->
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold text-gray-800 mb-2">短视频去水印下载</h1>
      <p class="text-gray-500">支持抖音、B站视频解析下载</p>
    </div>

    <!-- 输入区域 -->
    <div class="bg-white rounded-xl shadow-lg p-6 mb-6">
      <div class="flex gap-4">
        <input
          v-model="videoUrl"
          type="text"
          placeholder="粘贴视频链接..."
          class="flex-1 px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          @keyup.enter="handleParse"
        />
        <button
          @click="handleParse"
          :disabled="loading"
          class="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 transition"
        >
          {{ loading ? '解析中...' : '解析' }}
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="bg-red-50 text-red-600 p-4 rounded-lg mb-6">
      {{ error }}
    </div>

    <!-- 结果展示 -->
    <div v-if="result" class="bg-white rounded-xl shadow-lg p-6">
      <div class="flex gap-6">
        <!-- 封面 -->
        <div v-if="result.cover_url" class="w-48 h-28 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
          <img :src="result.cover_url" alt="封面" class="w-full h-full object-cover" />
        </div>
        <!-- 信息 -->
        <div class="flex-1">
          <h3 class="text-lg font-semibold text-gray-800 mb-2">{{ result.title }}</h3>
          <div class="flex items-center gap-4 text-sm text-gray-500 mb-4">
            <span class="px-2 py-1 bg-blue-100 text-blue-600 rounded">{{ result.platform }}</span>
            <span v-if="result.duration">{{ result.duration }}秒</span>
          </div>
          <button
            @click="handleDownload"
            class="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
          >
            下载视频
          </button>
        </div>
      </div>
    </div>
  </div>
</template>