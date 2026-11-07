import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

// html:false —— 用户内容里的原始 HTML 一律不渲染，防 XSS
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(code: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(code, { language: lang }).value}</code></pre>`
      } catch { /* 代码块未闭合时跳过 */ }
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(code)}</code></pre>`
  },
})

export const renderMarkdown = (text: string) => md.render(text || '')

/** 流式期间只做纯文本转义，避免每来一个字就跑一次语法高亮 */
export const renderPlain = (text: string) =>
  `<pre class="stream-plain">${md.utils.escapeHtml(text || '')}</pre>`
