// Me · 自知 — PWA Service Worker
// 缓存策略：Network First + Cache Fallback（PWA 离线可用）
const CACHE_NAME = 'me-v15'

self.addEventListener('install', (event) => {
  // 立即激活，不等待其他标签页关闭
  self.skipWaiting()
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(['/', '/index.html', '/manifest.json'])
    })
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      // 清除所有旧版本缓存
      const keys = await caches.keys()
      await Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
      // 立即接管所有客户端
      await self.clients.claim()
    })()
  )
})

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const clone = response.clone()
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone))
        return response
      })
      .catch(() => caches.match(event.request))
  )
})
