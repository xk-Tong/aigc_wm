import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 300000,
})

const NO_AUTH_URLS = ['/api/v1/auth/login', '/api/v1/auth/register']

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    const requestUrl = config.url || ''

    if (token && !NO_AUTH_URLS.some((path) => requestUrl.includes(path))) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => response,
  (error) => {
    const statusCode = error?.response?.status
    if (statusCode === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export default request
