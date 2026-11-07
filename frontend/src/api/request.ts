import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: '/api', timeout: 30000 })

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('yy_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (res) => {
    const data = res.data
    if (data && typeof data === 'object' && 'code' in data && data.code !== 0) {
      ElMessage.error(data.msg || '请求失败')
      return Promise.reject(new Error(data.msg))
    }
    if (res.status === 401) {
      localStorage.removeItem('yy_token')
      localStorage.removeItem('yy_role')
    }
    return data
  },
  (err) => {
    const status = err.response?.status
    if (status === 401) {
      localStorage.removeItem('yy_token')
      localStorage.removeItem('yy_role')
      ElMessage.error('请先登录')
    } else {
      ElMessage.error(err.response?.data?.msg || err.message || '网络异常')
    }
    return Promise.reject(err)
  },
)

export const get = (url: string, params?: any) => http.get(url, { params })
export const post = (url: string, data?: any, params?: any) => http.post(url, data, { params })
export const put = (url: string, data?: any, params?: any) => http.put(url, data, { params })
export const del = (url: string, params?: any) => http.delete(url, { params })

/** POST 不能用 EventSource，这里用 fetch 读 SSE 流，按 \n\n 拆包。 */
export async function streamChat(body: any, onEvent: (ev: any) => void) {
  const token = localStorage.getItem('yy_token')
  const resp = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  })
  if (!resp.ok || !resp.body) throw new Error(`SSE 请求失败: ${resp.status}`)
  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''
    for (const part of parts) {
      const line = part.split('\n').find((l) => l.startsWith('data:'))
      if (!line) continue
      try {
        onEvent(JSON.parse(line.slice(5).trim()))
      } catch {
        // 半包 / 粘包，忽略并等待后续数据
      }
    }
  }
}

export default http
