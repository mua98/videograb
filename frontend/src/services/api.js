import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const parseVideo = (url) => api.post('/parse', { url })

export const buildDownloadUrl = (videoUrl) => `/api/v1/download?url=${encodeURIComponent(videoUrl)}`