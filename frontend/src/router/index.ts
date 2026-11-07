import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const L = (path: string, name: string, component: () => Promise<any>, meta: any = {}) =>
  ({ path, name, component, meta } as RouteRecordRaw)

const crudConfigs: Record<string, any> = {
  categories: {
    api: '/categories', title: '分类管理',
    columns: [{ prop: 'id', label: 'ID', width: 80 }, { prop: 'name', label: '名称' },
              { prop: 'icon', label: '图标' }, { prop: 'sort', label: '排序' }],
    form: [{ prop: 'name', label: '分类名称', required: true },
           { prop: 'icon', label: '图标 URL' },
           { prop: 'sort', label: '排序', type: 'number' }],
  },
  products: {
    api: '/products', title: '商品管理',
    columns: [{ prop: 'id', label: 'ID', width: 70 }, { prop: 'title', label: '商品名称' },
              { prop: 'price', label: '价格', width: 100 }, { prop: 'stock', label: '库存', width: 90 },
              { prop: 'sales', label: '销量', width: 90 }, { prop: 'status', label: '上架', type: 'tag', width: 90 }],
    form: [{ prop: 'title', label: '商品名称', required: true },
           { prop: 'subtitle', label: '副标题' },
           { prop: 'category_id', label: '分类', type: 'category' },
           { prop: 'price', label: '售价', type: 'number' },
           { prop: 'original_price', label: '原价', type: 'number' },
           { prop: 'stock', label: '库存', type: 'number' },
           { prop: 'cover', label: '封面图', type: 'image' },
           { prop: 'status', label: '上架', type: 'switch' },
           { prop: 'detail', label: '图文详情', type: 'richtext' }],
  },
  orders: {
    api: '/admin/orders', title: '订单管理', readonly: true,
    columns: [{ prop: 'order_no', label: '订单号' }, { prop: 'total_amount', label: '金额', width: 110 },
              { prop: 'status', label: '状态', type: 'status', width: 110 },
              { prop: 'created_at', label: '下单时间', width: 190 }],
  },
  reviews: {
    api: '/admin/reviews', title: '评价管理', readonly: true, deletable: true,
    columns: [{ prop: 'id', label: 'ID', width: 70 }, { prop: 'user', label: '用户', width: 130 },
              { prop: 'product_id', label: '商品ID', width: 100 },
              { prop: 'rating', label: '评分', width: 90 }, { prop: 'content', label: '内容' }],
  },
  news: {
    api: '/news', title: '资讯管理',
    columns: [{ prop: 'id', label: 'ID', width: 70 }, { prop: 'title', label: '标题' },
              { prop: 'views', label: '浏览量', width: 100 }, { prop: 'status', label: '发布', type: 'tag', width: 90 }],
    form: [{ prop: 'title', label: '标题', required: true },
           { prop: 'cover', label: '封面图', type: 'image' },
           { prop: 'summary', label: '摘要', type: 'textarea' },
           { prop: 'status', label: '发布', type: 'switch' },
           { prop: 'content', label: '正文', type: 'richtext' }],
  },
  banners: {
    api: '/banners', title: '轮播图管理',
    columns: [{ prop: 'id', label: 'ID', width: 70 }, { prop: 'title', label: '标题' },
              { prop: 'image', label: '图片', type: 'image' }, { prop: 'sort', label: '排序', width: 90 }],
    form: [{ prop: 'title', label: '标题' }, { prop: 'image', label: '图片', type: 'image' },
           { prop: 'link', label: '跳转链接' }, { prop: 'sort', label: '排序', type: 'number' },
           { prop: 'status', label: '启用', type: 'switch' }],
  },
  notices: {
    api: '/notices', title: '公告管理',
    columns: [{ prop: 'id', label: 'ID', width: 70 }, { prop: 'title', label: '标题' },
              { prop: 'content', label: '内容' }],
    form: [{ prop: 'title', label: '标题', required: true },
           { prop: 'content', label: '内容', type: 'textarea' },
           { prop: 'status', label: '启用', type: 'switch' }],
  },
  admins: {
    api: '/admin/admins', title: '管理员管理', custom: 'admins',
    columns: [{ prop: 'id', label: 'ID', width: 70 }, { prop: 'username', label: '账号' },
              { prop: 'nickname', label: '昵称' }, { prop: 'status', label: '状态', type: 'tag', width: 90 }],
  },
  members: {
    api: '/admin/members', title: '会员管理', custom: 'members',
    columns: [{ prop: 'id', label: 'ID', width: 70 }, { prop: 'username', label: '账号' },
              { prop: 'nickname', label: '昵称' }, { prop: 'phone', label: '手机' },
              { prop: 'status', label: '状态', type: 'tag', width: 90 }],
  },
}

const routes: RouteRecordRaw[] = [
  {
    path: '/', component: () => import('../views/front/FrontLayout.vue'),
    children: [
      L('', 'home', () => import('../views/front/Home.vue')),
      L('products', 'products', () => import('../views/front/Products.vue')),
      L('products/:id', 'product-detail', () => import('../views/front/ProductDetail.vue')),
      L('cart', 'cart', () => import('../views/front/Cart.vue'), { requiresAuth: true }),
      L('checkout', 'checkout', () => import('../views/front/Checkout.vue'), { requiresAuth: true }),
      L('orders', 'orders', () => import('../views/front/Orders.vue'), { requiresAuth: true }),
      L('news', 'news', () => import('../views/front/News.vue')),
      L('news/:id', 'news-detail', () => import('../views/front/NewsDetail.vue')),
      L('ai', 'ai', () => import('../views/front/AIAssistant.vue')),
      L('login', 'login', () => import('../views/front/Login.vue')),
      L('profile', 'profile', () => import('../views/front/Profile.vue'), { requiresAuth: true }),
      L('favorites', 'favorites', () => import('../views/front/Favorites.vue'), { requiresAuth: true }),
    ],
  },
  { path: '/admin/login', name: 'admin-login', component: () => import('../views/front/Login.vue'),
    meta: { adminLogin: true } },
  {
    path: '/admin', component: () => import('../views/admin/AdminLayout.vue'),
    meta: { requiresAdmin: true },
    children: [
      L('', 'admin-dashboard', () => import('../views/admin/Dashboard.vue')),
      ...Object.keys(crudConfigs).map(k =>
        L(k, 'admin-' + k, () => import('../views/admin/GenericList.vue'), { crud: crudConfigs[k] })),
      L('models', 'admin-models', () => import('../views/admin/ModelConfig.vue')),
      L('prompts', 'admin-prompts', () => import('../views/admin/PromptConfig.vue')),
      L('knowledge', 'admin-knowledge', () => import('../views/admin/Knowledge.vue')),
      L('chat-records', 'admin-chat-records', () => import('../views/admin/ChatRecords.vue')),
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const token = localStorage.getItem('yy_token')
  const role = localStorage.getItem('yy_role')
  if (to.meta.requiresAdmin && (role !== 'admin' || !token)) {
    return { path: '/admin/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAuth && !token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
