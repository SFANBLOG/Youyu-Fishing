<template>
  <div class="rich-editor">
    <Toolbar :editor="editorRef" :defaultConfig="toolbarConfig" mode="default" />
    <Editor :defaultConfig="editorConfig" mode="default" v-model="valueHtml"
            style="height: 320px; overflow-y: hidden" @onCreated="onCreated" />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, shallowRef } from 'vue'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import { api } from '../api'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits(['update:modelValue'])

const editorRef = shallowRef()
const valueHtml = computed({
  get: () => props.modelValue || '',
  set: (v: string) => emit('update:modelValue', v),
})
const toolbarConfig = {}
const editorConfig = {
  MENU_CONF: {
    uploadImage: {
      server: api.uploadUrl,
      fieldName: 'file',
      headers: { Authorization: `Bearer ${localStorage.getItem('yy_token') || ''}` },
      // wangEditor 要求返回 {errno, data:[{url}]}
      customInsert(res: any, insertFn: any) {
        const item = Array.isArray(res.data) ? res.data[0] : res.data
        insertFn(item.url, item.alt || '', item.href || item.url)
      },
    },
  },
}
const onCreated = (editor: any) => { editorRef.value = editor }
onBeforeUnmount(() => editorRef.value?.destroy())
</script>

<style scoped>
.rich-editor { border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
</style>
