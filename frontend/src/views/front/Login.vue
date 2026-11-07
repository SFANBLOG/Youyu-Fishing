<template>
  <div style="max-width:420px;margin:60px auto" class="card">
    <div style="padding:28px">
      <h2 style="text-align:center;margin:0 0 6px">{{ isAdmin ? '后台管理员登录' : '欢迎回来' }}</h2>
      <p class="muted" style="text-align:center">{{ isAdmin ? '请使用管理员账号' : '登录后可结算、收藏与保存 AI 对话' }}</p>
      <el-tabs v-model="tab" v-if="!isAdmin">
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>
      <el-form @submit.prevent="submit">
        <el-form-item><el-input v-model="username" placeholder="用户名" size="large" /></el-form-item>
        <el-form-item v-if="tab === 'register' && !isAdmin">
          <el-input v-model="nickname" placeholder="昵称（选填）" size="large" />
        </el-form-item>
        <el-form-item><el-input v-model="password" type="password" placeholder="密码" size="large" show-password /></el-form-item>
        <el-button type="primary" size="large" style="width:100%" @click="submit">
          {{ isAdmin || tab === 'login' ? '登录' : '注册' }}
        </el-button>
      </el-form>
      <div class="muted" style="margin-top:14px;text-align:center">
        {{ isAdmin ? 'admin / 123456' : '测试账号 user / 123456' }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../../api'

const route = useRoute()
const router = useRouter()
const isAdmin = computed(() => route.meta.adminLogin === true)
const tab = ref('login')
const username = ref(''), password = ref(''), nickname = ref('')

async function submit() {
  try {
    const res: any = tab.value === 'register' && !isAdmin.value
      ? await api.register({ username: username.value, password: password.value, nickname: nickname.value })
      : await api.login({ username: username.value, password: password.value })
    const { token, user } = res.data
    if (isAdmin.value && user.role !== 'admin') {
      ElMessage.error('该账号不是管理员')
      return
    }
    localStorage.setItem('yy_token', token)
    localStorage.setItem('yy_role', user.role)
    localStorage.setItem('yy_user', JSON.stringify(user))
    ElMessage.success('登录成功')
    router.push((route.query.redirect as string) || (isAdmin.value ? '/admin' : '/'))
  } catch (e: any) {
    ElMessage.error(e.response?.data?.msg || '操作失败')
  }
}
</script>
