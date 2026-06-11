import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import { createPinia } from 'pinia'
import App from './App.vue'
import './style.css'

// Lazy-loaded views（首屏后自动预加载）
const ChatView = () => import('./views/ChatView.vue')
const ArchiveView = () => import('./views/ArchiveView.vue')
const ArchiveDetailView = () => import('./views/ArchiveDetailView.vue')
const ReportView = () => import('./views/ReportView.vue')
const SkillsView = () => import('./views/SkillsView.vue')
const ExpertConfigView = () => import('./views/ExpertConfigView.vue')
const SettingsView = () => import('./views/SettingsView.vue')
const DaobenView = () => import('./views/DaobenView.vue')
const DaobenDashboardView = () => import('./views/DaobenDashboardView.vue')
const UploadsView = () => import('./views/UploadsView.vue')

// 预加载所有路由页面 chunk（首屏渲染后后台执行，切换页面秒开）
const ALL_CHUNKS = [
  import('./views/ChatView.vue'),
  import('./views/ArchiveView.vue'),
  import('./views/ArchiveDetailView.vue'),
  import('./views/ReportView.vue'),
  import('./views/SkillsView.vue'),
  import('./views/ExpertConfigView.vue'),
  import('./views/SettingsView.vue'),
  import('./views/DaobenView.vue'),
  import('./views/DaobenDashboardView.vue'),
  import('./views/UploadsView.vue'),
]
const routes = [
  { path: '/', redirect: '/chat' },
  { path: '/chat', component: ChatView, meta: { title: '对话', icon: '💬' } },
  { path: '/archive', component: ArchiveView, meta: { title: '档案馆', icon: '📚' } },
  { path: '/archive/uploads', component: UploadsView, meta: { title: '导入文件' } },
  { path: '/archive/:id', component: ArchiveDetailView, meta: { title: '档案详情' } },
  { path: '/report', component: ReportView, meta: { title: '复盘', icon: '📋' } },
  { path: '/skills', component: SkillsView, meta: { title: '技能', icon: '🔧' } },
  { path: '/daoben', component: DaobenView, meta: { title: '道痕', icon: '🪨' } },
  { path: '/daoben/dashboard', component: DaobenDashboardView, meta: { title: '回看仪表盘' } },
  { path: '/experts', component: ExpertConfigView, meta: { title: '专家', icon: '🎭' } },
  { path: '/settings', component: SettingsView, meta: { title: '设置', icon: '⚙️' } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

const app = createApp(App)
app.use(router)
app.use(createPinia())
app.mount('#app')

// PWA Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {})
  })
}
