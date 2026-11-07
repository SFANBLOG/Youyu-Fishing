<template>
  <div style="display:flex;gap:16px;margin-top:18px">
    <aside class="card" style="width:220px;padding:12px;flex-shrink:0">
      <el-button type="primary" style="width:100%" @click="newSession">＋ 新会话</el-button>
      <div v-for="s in sessions" :key="s.id" class="session-item"
           :class="{active: sessionId === s.id}" @click="openSession(s.id)">
        {{ s.title }}
      </div>
      <el-empty v-if="!sessions.length" description="暂无会话" :image-size="50" />
    </aside>

    <section class="card" style="flex:1;min-width:0;display:flex;flex-direction:column;height:calc(100vh - 190px)">
      <div style="padding:12px 16px;border-bottom:1px solid #f3f4f6;display:flex;justify-content:space-between;align-items:center">
        <b>AI 选竿助手</b>
        <el-button text type="primary" @click="traceDrawer = true">执行轨迹</el-button>
      </div>

      <div ref="scrollEl" class="chat-scroll">
        <template v-for="(m, i) in messages" :key="i">
          <AiBubble :role="m.role" :text="m.content" :streaming="m.streaming"
                    :images="m.images" :recommendations="m.recommendations"
                    :sources="m.sources" :meta="m.meta" :degraded="m.degraded" />
        </template>
        <div v-if="!messages.length" style="text-align:center;margin-top:60px">
          <h3>问点什么吧</h3>
          <div class="muted" style="margin-bottom:16px">支持查知识、搜商品、求推荐、上传装备图片识别</div>
          <el-button v-for="q in quick" :key="q" size="small" style="margin:4px" @click="ask(q)">{{ q }}</el-button>
        </div>
      </div>

      <div style="padding:12px 16px;border-top:1px solid #f3f4f6">
        <div v-if="images.length" style="display:flex;gap:8px;margin-bottom:8px">
          <div v-for="(img,i) in images" :key="i" style="position:relative">
            <img :src="img" style="width:64px;height:64px;object-fit:cover;border-radius:6px" />
            <el-button size="small" circle style="position:absolute;right:-6px;top:-6px" @click="images.splice(i,1)">×</el-button>
          </div>
        </div>
        <div style="display:flex;gap:8px;align-items:flex-end">
          <label class="upload-btn">
            <input type="file" accept="image/*" multiple hidden @change="onFiles" />
            <el-icon><Picture /></el-icon>
          </label>
          <el-input v-model="input" type="textarea" :rows="2" placeholder="例如：新手野钓选什么调性的竿？"
                    @keyup.enter.exact.prevent="send" />
          <el-button type="primary" :loading="loading" @click="send">发送</el-button>
        </div>
      </div>
    </section>

    <el-drawer v-model="traceDrawer" title="Agent 执行轨迹（可解释性）" size="480px">
      <el-timeline>
        <el-timeline-item v-for="(t,i) in lastTrace" :key="i" :timestamp="String(t.ts)">
          <b>{{ t.node }}</b>：{{ t.detail }}
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!lastTrace.length" description="发一条消息后可见" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { Picture } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { streamChat } from '../../api/request'
import { api } from '../../api'
import AiBubble from '../../components/AiBubble.vue'

const quick = ['新手选什么调性的竿？', '推荐 500 元以内的路亚竿', '路亚拟饵怎么搭配？', '帮我查一下订单']
const input = ref('')
const images = ref<string[]>([])
const messages = ref<any[]>([])
const sessions = ref<any[]>([])
const sessionId = ref<number | null>(null)
const loading = ref(false)
const traceDrawer = ref(false)
const lastTrace = ref<any[]>([])
const scrollEl = ref<HTMLElement>()

async function loadSessions() {
  if (!localStorage.getItem('yy_token')) return
  const r: any = await api.sessions()
  sessions.value = r.data || []
}
function newSession() {
  sessionId.value = null
  messages.value = []
  lastTrace.value = []
  input.value = ''
}
async function openSession(id: number) {
  sessionId.value = id
  const r: any = await api.messages(id)
  messages.value = (r.data || []).map((m: any) => ({
    role: m.role, content: m.content, images: m.images,
    recommendations: m.recommendations, sources: m.sources,
    degraded: m.degraded, streaming: false,
    meta: m.role === 'assistant'
      ? `意图 ${m.intent || '-'} · 工具 ${m.tool || '-'} · 引擎 ${m.engine || '-'}` : '',
  }))
  lastTrace.value = [...(r.data || [])].reverse().find((m: any) => m.trace?.length)?.trace || []
  scroll()
}
function onFiles(e: any) {
  const files: File[] = Array.from(e.target.files || [])
  files.slice(0, 3).forEach((f) => {
    const reader = new FileReader()
    reader.onload = () => images.value.push(String(reader.result))
    reader.readAsDataURL(f)
  })
  e.target.value = ''
}
function ask(q: string) { input.value = q; send() }
function scroll() { nextTick(() => { if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight }) }

async function send() {
  const text = input.value.trim()
  if (!text && !images.value.length) return
  if (loading.value) return
  loading.value = true
  const imgs = [...images.value]
  messages.value.push({ role: 'user', content: text, images: imgs })
  const ai: any = { role: 'assistant', content: '', streaming: true,
                    recommendations: [], sources: [], meta: '' }
  messages.value.push(ai)
  input.value = ''
  images.value = []
  scroll()

  try {
    await streamChat({ message: text, session_id: sessionId.value, images: imgs }, (ev) => {
      if (ev.type === 'meta') {
        sessionId.value = ev.session_id
        loadSessions()
      } else if (ev.type === 'delta') {
        ai.content += ev.text
        scroll()
      } else if (ev.type === 'done') {
        ai.streaming = false
        ai.content = ev.answer || ai.content
        ai.recommendations = ev.recommendations || []
        ai.sources = ev.sources || []
        ai.degraded = ev.degraded
        ai.meta = `意图 ${ev.intent || '-'} · 工具 ${ev.tool || '-'} · 引擎 ${ev.engine || '-'}`
        lastTrace.value = ev.trace || []
        scroll()
      } else if (ev.type === 'error') {
        ai.streaming = false
        ai.content = ev.message
      }
    })
  } catch (e: any) {
    ai.streaming = false
    ai.content = ai.content || `请求失败：${e.message}`
    ElMessage.error('AI 服务暂时不可用')
  } finally {
    loading.value = false
    scroll()
  }
}
onMounted(loadSessions)
</script>

<style scoped>
.session-item { padding: 10px 8px; border-radius: 8px; cursor: pointer; font-size: 13px; margin-top: 8px; }
.session-item:hover { background: #f3f4f6; }
.session-item.active { background: #ccfbf1; color: #0f766e; font-weight: 600; }
.upload-btn { display: inline-flex; align-items: center; justify-content: center; width: 42px; height: 56px;
  border: 1px solid #d1d5db; border-radius: 8px; cursor: pointer; font-size: 20px; }
</style>
