import { del, get, post, put } from './request'

export const api = {
  // 认证
  login: (d: any) => post('/auth/login', d),
  register: (d: any) => post('/auth/register', d),
  me: () => get('/auth/me'),

  // 商城
  categories: () => get('/categories'),
  createCategory: (name: string, icon = '', sort = 0) => post('/categories', null, { name, icon, sort }),
  updateCategory: (id: number, d: any) => put(`/categories/${id}`, null, d),
  deleteCategory: (id: number) => del(`/categories/${id}`),
  products: (p: any) => get('/products', p),
  product: (id: number) => get(`/products/${id}`),
  similar: (id: number) => get(`/products/${id}/similar`),
  createProduct: (d: any) => post('/products', d),
  updateProduct: (id: number, d: any) => put(`/products/${id}`, d),
  deleteProduct: (id: number) => del(`/products/${id}`),
  favorites: () => get('/favorites'),
  addFavorite: (product_id: number) => post('/favorites', null, { product_id }),
  removeFavorite: (product_id: number) => del(`/favorites/${product_id}`),

  // 交易
  cart: () => get('/cart'),
  addCart: (d: any) => post('/cart', d),
  updateCart: (id: number, d: any) => put(`/cart/${id}`, null, d),
  checkAll: (checked: boolean) => post('/cart/check-all', null, { checked }),
  batchDeleteCart: (ids: number[]) => post('/cart/batch-delete', { ids }),
  clearCart: () => del('/cart'),
  createOrder: (d: any) => post('/orders', d),
  orders: (p: any) => get('/orders', p),
  orderStatus: (id: number, status: string) => put(`/orders/${id}/status`, { status }),
  reviews: (p: any) => get('/reviews', p),
  createReview: (d: any) => post('/reviews', d),
  deleteReview: (id: number) => del(`/reviews/${id}`),

  // 内容
  news: (p: any) => get('/news', p),
  newsDetail: (id: number) => get(`/news/${id}`),
  createNews: (d: any) => post('/news', d),
  updateNews: (id: number, d: any) => put(`/news/${id}`, d),
  deleteNews: (id: number) => del(`/news/${id}`),
  banners: () => get('/banners'),
  createBanner: (d: any) => post('/banners', d),
  updateBanner: (id: number, d: any) => put(`/banners/${id}`, d),
  deleteBanner: (id: number) => del(`/banners/${id}`),
  notices: () => get('/notices'),
  createNotice: (d: any) => post('/notices', d),
  updateNotice: (id: number, d: any) => put(`/notices/${id}`, d),
  deleteNotice: (id: number) => del(`/notices/${id}`),
  uploadUrl: '/api/upload',

  // 后台
  admins: () => get('/admin/admins'),
  createAdmin: (d: any) => post('/admin/admins', null, d),
  adminStatus: (id: number, status: boolean) => put(`/admin/admins/${id}/status`, null, { status }),
  members: (p: any) => get('/admin/members', p),
  memberStatus: (id: number, status: boolean) => put(`/admin/members/${id}/status`, null, { status }),
  dashboard: () => get('/admin/dashboard'),
  chatRecords: (p: any) => get('/admin/chat/records', p),

  // AI 能力中心
  models: () => get('/ai/models'),
  createModel: (d: any) => post('/ai/models', d),
  updateModel: (id: number, d: any) => put(`/ai/models/${id}`, d),
  deleteModel: (id: number) => del(`/ai/models/${id}`),
  testModel: (id: number) => post(`/ai/models/${id}/test`),
  setDefaultModel: (id: number) => post(`/ai/models/${id}/default`),
  prompts: () => get('/ai/prompts'),
  updatePrompt: (id: number, d: any) => put(`/ai/prompts/${id}`, d),
  previewPrompt: (id: number, variables: any) => post(`/ai/prompts/${id}/preview`, { variables }),
  docs: () => get('/knowledge/docs'),
  doc: (id: number) => get(`/knowledge/docs/${id}`),
  createDoc: (d: any) => post('/knowledge/docs', d),
  updateDoc: (id: number, d: any) => put(`/knowledge/docs/${id}`, d),
  deleteDoc: (id: number) => del(`/knowledge/docs/${id}`),
  chunks: (id: number) => get(`/knowledge/docs/${id}/chunks`),
  reindex: (id: number) => post(`/knowledge/docs/${id}/reindex`),
  searchTest: (d: any) => post('/knowledge/search-test', d),

  // 对话
  sessions: () => get('/chat/sessions'),
  messages: (sid: number) => get(`/chat/sessions/${sid}/messages`),
  deleteSession: (sid: number) => del(`/chat/sessions/${sid}`),
}
