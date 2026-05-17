import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

export const parseVideo = (url) => api.post('/parse', { url })

export const downloadVideo = (videoUrl) => `/api/v1/download?url=${encodeURIComponent(videoUrl)}`