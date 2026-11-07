<template>
  <div class="card" style="padding:18px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
      <h2 style="margin:0">{{ cfg.title }}</h2>
      <div>
        <el-input v-if="cfg.custom === 'members'" v-model="keyword" placeholder="搜账号"
                  style="width:180px;margin-right:8px" @keyup.enter="load" />
        <el-button v-if="cfg.form || cfg.custom === 'admins'" type="primary" @click="openForm()">新增</el-button>
      </div>
    </div>

    <el-table :data="rows" border stripe v-loading="loading">
      <el-table-column v-for="c in cfg.columns" :key="c.prop" :prop="c.prop" :label="c.label"
                       :width="c.width" show-overflow-tooltip>
        <template #default="{ row }">
          <img v-if="c.type === 'image' && row[c.prop]" :src="row[c.prop]"
               style="width:54px;height:40px;object-fit:cover;border-radius:4px" />
          <el-tag v-else-if="c.type === 'tag'" :type="row[c.prop] ? 'success' : 'info'">
            {{ row[c.prop] ? '启用' : '停用' }}
          </el-tag>
          <el-tag v-else-if="c.type === 'status'" :type="statusTag(row[c.prop])">
            {{ statusText(row[c.prop]) }}
          </el-tag>
          <span v-else>{{ row[c.prop] }}</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button v-if="cfg.form" size="small" @click="openForm(row)">编辑</el-button>
          <el-select v-if="cfg.api === '/admin/orders'" :model-value="row.status" size="small"
                     style="width:110px;margin-right:6px" @change="(v:any) => setOrderStatus(row, v)">
            <el-option v-for="s in ['pending','paid','shipped','completed','cancelled']" :key="s"
                       :label="statusText(s)" :value="s" />
          </el-select>
          <el-button v-if="cfg.custom === 'admins' || cfg.custom === 'members'" size="small"
                     @click="toggleUser(row)">{{ row.status ? '停用' : '启用' }}</el-button>
          <el-button v-if="cfg.deletable || cfg.form" size="small" type="danger" plain
                     @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:14px">
      <el-pagination background layout="total, sizes, prev, pager, next, jumper"
                     :total="total" v-model:current-page="page" v-model:page-size="size"
                     :page-sizes="[10, 20, 50]" @current-change="load" @size-change="load" />
    </div>

    <el-dialog v-model="dialog" :title="(editing ? '编辑' : '新增') + cfg.title" width="640px">
      <el-form label-width="100px">
        <el-form-item v-for="f in cfg.form" :key="f.prop" :label="f.label">
          <el-input v-if="!f.type || f.type === 'text'" v-model="form[f.prop]" />
          <el-input v-else-if="f.type === 'textarea'" v-model="form[f.prop]" type="textarea" :rows="3" />
          <el-input-number v-else-if="f.type === 'number'" v-model="form[f.prop]" />
          <el-switch v-else-if="f.type === 'switch'" v-model="form[f.prop]" />
          <el-select v-else-if="f.type === 'category'" v-model="form[f.prop]" style="width:100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <div v-else-if="f.type === 'image'">
            <el-upload :show-file-list="false" :http-request="(o:any) => uploadImage(o, f.prop)">
              <el-button size="small">上传图片</el-button>
            </el-upload>
            <img v-if="form[f.prop]" :src="form[f.prop]" style="width:120px;height:80px;object-fit:cover;margin-top:8px" />
          </div>
          <RichEditor v-else-if="f.type === 'richtext'" v-model="form[f.prop]" />
        </el-form-item>
        <el-form-item v-if="cfg.custom === 'admins'" label="密码">
          <el-input v-model="password" type="password" placeholder="新增时必填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { get, post, put, del } from '../../api/request'
import { api } from '../../api'
import RichEditor from '../../components/RichEditor.vue'

const route = useRoute()
const cfg: any = route.meta.crud
const rows = ref<any[]>([])
const total = ref(0), page = ref(1), size = ref(10)
const keyword = ref('')
const loading = ref(false)
const dialog = ref(false)
const editing = ref(false)
const form = ref<any>({})
const password = ref('')
const categories = ref<any[]>([])

const statusText = (s: string) => ({ pending: '待支付', paid: '已支付', shipped: '已发货',
                                     completed: '已完成', cancelled: '已取消' } as any)[s] || s
const statusTag = (s: string) => ({ pending: 'warning', paid: 'primary', shipped: 'info',
                                    completed: 'success', cancelled: 'danger' } as any)[s] || 'info'

async function load() {
  loading.value = true
  try {
    const res: any = await get(cfg.api, { page: page.value, size: size.value, keyword: keyword.value,
                                          only_online: false })
    const d = res.data
    rows.value = Array.isArray(d) ? d : (d?.items || [])
    total.value = Array.isArray(d) ? rows.value.length : (d?.total || 0)
  } finally {
    loading.value = false
  }
}

function openForm(row?: any) {
  editing.value = !!row
  password.value = ''
  form.value = row ? { ...row } : Object.fromEntries(
    (cfg.form || []).map((f: any) => [f.prop, f.type === 'switch' ? true :
      f.type === 'number' ? 0 : f.type === 'richtext' ? '' : '']))
  dialog.value = true
}

async function uploadImage(opt: any, prop: string) {
  const fd = new FormData()
  fd.append('file', opt.file)
  const r = await axios.post(api.uploadUrl, fd, {
    headers: { Authorization: `Bearer ${localStorage.getItem('yy_token') || ''}` },
  })
  form.value[prop] = r.data.url
  ElMessage.success('上传成功')
}

async function save() {
  const id = form.value.id
  try {
    if (cfg.custom === 'admins' && !editing.value) {
      await api.createAdmin({ username: form.value.username, password: password.value,
                              nickname: form.value.nickname })
    } else if (cfg.api === '/categories') {
      const payload = { name: form.value.name, icon: form.value.icon || '', sort: form.value.sort || 0 }
      if (editing.value) await put(`/categories/${id}`, null, payload)
      else await post('/categories', null, payload)
    } else if (editing.value) {
      await put(`${cfg.api}/${id}`, form.value)
    } else {
      await post(cfg.api, form.value)
    }
    ElMessage.success('保存成功')
    dialog.value = false
    load()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.msg || '保存失败')
  }
}

async function remove(row: any) {
  const path = cfg.api === '/admin/reviews' ? `/reviews/${row.id}` : `${cfg.api}/${row.id}`
  await del(path)
  ElMessage.success('已删除')
  load()
}
async function toggleUser(row: any) {
  const base = cfg.custom === 'admins' ? 'admins' : 'members'
  await put(`/admin/${base}/${row.id}/status`, null, { status: !row.status })
  load()
}
async function setOrderStatus(row: any, status: string) {
  await put(`/admin/orders/${row.id}/status`, null, { status })
  ElMessage.success('状态已更新')
  load()
}
onMounted(async () => {
  if ((cfg.form || []).some((f: any) => f.type === 'category')) {
    const r: any = await api.categories()
    categories.value = r.data || []
  }
  load()
})
</script>
