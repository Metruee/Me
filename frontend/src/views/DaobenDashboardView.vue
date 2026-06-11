<template>
  <div class="page">
    <header class="page-header">📊 道痕回看</header>
    <div style="text-align:center;font-size:11px;color:var(--ink-muted);margin-bottom:var(--space-lg);">
      每天捞一块石头，每周回头看一眼——你会发现自己比想象中简单
    </div>

    <!-- Period Toggle -->
    <div class="filter-row" style="margin-bottom:var(--space-lg)">
      <button class="filter-tag" :class="{ active: period === 'week' }" @click="load('week')">本周</button>
      <button class="filter-tag" :class="{ active: period === 'month' }" @click="load('month')">本月</button>
      <button class="filter-tag" :class="{ active: period === 'all' }" @click="load('all')">全部</button>
    </div>

    <div v-if="loading" class="empty-state">加载中…</div>

    <template v-else-if="data && data.total > 0">
      <!-- Summary Cards -->
      <div class="summary-row">
        <div class="summary-card">
          <div class="summary-num">{{ data.total }}</div>
          <div class="summary-label">道痕记录</div>
        </div>
        <div class="summary-card">
          <div class="summary-num">{{ data.stones.length }}</div>
          <div class="summary-label">不同心石</div>
        </div>
        <div class="summary-card" :class="trendClass">
          <div class="summary-num">{{ data.trend_label }}</div>
          <div class="summary-label">分布趋势</div>
        </div>
        <div class="summary-card" :class="balanceClass">
          <div class="summary-num">{{ data.greed_fear_label }}</div>
          <div class="summary-label">贪惧天平</div>
        </div>
      </div>

      <!-- Stones -->
      <div class="card" style="margin-bottom:var(--space-lg)">
        <h3 style="font-size:var(--text-title);margin-bottom:var(--space-md);color:var(--ink)">🪨 重复心石 Top 10</h3>
        <p style="font-size:var(--text-caption);color:var(--ink-muted);margin-bottom:var(--space-md)">
          如果一块石头反复出现，它不是偶发情绪，是你河底的大石头
        </p>
        <div v-if="!data.stones.length" style="color:var(--ink-muted);font-size:var(--text-caption)">暂无</div>
        <div v-else class="stone-list">
          <div v-for="(s, i) in data.stones" :key="i" class="stone-row">
            <div class="stone-rank">#{{ i + 1 }}</div>
            <div class="stone-name">{{ s.stone }}</div>
            <div class="stone-bar-wrap">
              <div class="stone-bar" :style="{ width: barPct(s.count) + '%' }"></div>
            </div>
            <div class="stone-count">×{{ s.count }}</div>
          </div>
        </div>
      </div>

      <!-- Greed-Fear Balance -->
      <div class="card" style="margin-bottom:var(--space-lg)">
        <h3 style="font-size:var(--text-title);margin-bottom:var(--space-sm);color:var(--ink)">⚖️ 贪 / 惧 天平</h3>
        <p style="font-size:var(--text-caption);color:var(--ink-muted);margin-bottom:var(--space-md)">
          贪梦让人伸手，恐惧让人缩手。如果一边彻底压倒另一边，桥就要断了。
        </p>
        <div class="balance-bar">
          <div class="balance-side balance-greed" :style="{ flex: greedFlex }">
            <span>贪梦 {{ data.greed_fear_ratio?.toFixed(1) || 0 }} : 1</span>
          </div>
          <div class="balance-side balance-fear" :style="{ flex: fearFlex }">
            <span>恐惧 1</span>
          </div>
        </div>
        <div style="margin-top:var(--space-sm);font-size:var(--text-caption);color:var(--ink-muted);text-align:center">
          {{ balanceAdvice }}
        </div>
      </div>

      <!-- Excuses -->
      <div class="card" v-if="data.excuses && data.excuses.length" style="margin-bottom:var(--space-lg)">
        <h3 style="font-size:var(--text-title);margin-bottom:var(--space-sm);color:var(--ink)">🌊 常用自洽理由</h3>
        <p style="font-size:var(--text-caption);color:var(--ink-muted);margin-bottom:var(--space-md)">
          你给自己编得最多的解释——真正的石头，往往藏在你最会讲的理由后面
        </p>
        <div v-for="(e, i) in data.excuses" :key="i" class="excuse-row">
          <span class="excuse-index">{{ i + 1 }}.</span>
          <span class="excuse-text">{{ e.excuse }}</span>
          <span class="excuse-count">×{{ e.count }}</span>
        </div>
      </div>

      <!-- Timeline -->
      <div class="card" v-if="data.timeline && data.timeline.length" style="margin-bottom:var(--space-lg)">
        <h3 style="font-size:var(--text-title);margin-bottom:var(--space-sm);color:var(--ink)">📅 记道痕频率</h3>
        <div class="timeline-chart">
          <div v-for="d in data.timeline" :key="d.date" class="timeline-bar-wrap">
            <div class="timeline-bar" :style="{ height: timelineH(d.count) + 'px' }" :title="d.date + ': ' + d.count + '条'"></div>
            <div class="timeline-label">{{ d.date.slice(5) }}</div>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="empty-state">
      <div style="font-size:48px;margin-bottom:var(--space-lg)">🪨</div>
      <h2 style="font-size:var(--text-headline);margin-bottom:var(--space-sm);color:var(--ink)">该时段暂无道痕</h2>
      <p style="color:var(--ink-muted);max-width:280px">
        先去记几笔道痕再回来看。每天捞一块石头，坚持一周，你会发现惊人的规律。
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface DashboardData {
  total: number
  period: string
  stones: { stone: string; count: number }[]
  greed_fear_ratio: number | null
  greed_fear_label: string
  excuses: { excuse: string; count: number }[]
  timeline: { date: string; count: number }[]
  trend: string
  trend_label: string
  message?: string
}

const period = ref('week')
const loading = ref(true)
const data = ref<DashboardData | null>(null)

const maxCount = computed(() => {
  if (!data.value?.stones.length) return 1
  return data.value.stones[0].count
})

const greedFlex = computed(() => {
  const ratio = data.value?.greed_fear_ratio
  if (ratio === null) return 1
  return Math.max(0.2, Math.min(ratio, 5))
})

const fearFlex = computed(() => 1)

const trendClass = computed(() => {
  const t = data.value?.trend
  return { 'trend-stable': t === 'stable', 'trend-skewed': t === 'skewed', 'trend-danger': t === 'dominated' }
})

const balanceClass = computed(() => {
  const r = data.value?.greed_fear_ratio
  if (r === null) return ''
  return r > 1.5 ? 'balance-greed-heavy' : r < 0.67 ? 'balance-fear-heavy' : 'balance-even'
})

const balanceAdvice = computed(() => {
  const r = data.value?.greed_fear_ratio
  if (r === null) return ''
  if (r > 2) return '⚠️ 贪梦远大于恐惧——你是不是一直在伸手，很少缩手？'
  if (r < 0.5) return '⚠️ 恐惧远大于贪梦——你是不是缩手太多，不敢伸手了？'
  if (r > 1.5) return '贪梦略多，记得也看看恐惧那边。'
  if (r < 0.67) return '恐惧略多，别忘了你心里还有想要的东西。'
  return '✅ 贪惧平衡，天权之桥还在。'
})

const maxTimeline = computed(() => {
  if (!data.value?.timeline.length) return 1
  return Math.max(...data.value.timeline.map(d => d.count))
})

function barPct(count: number) { return (count / maxCount.value) * 100 }
function timelineH(count: number) { return Math.max(4, (count / maxTimeline.value) * 80) }

async function load(p: string) {
  period.value = p
  loading.value = true
  try {
    const res = await fetch(`/api/daoben/dashboard?period=${p}`)
    data.value = await res.json()
  } catch { data.value = null }
  loading.value = false
}

onMounted(() => load('week'))
</script>

<style scoped>
.summary-row { display: flex; gap: var(--space-md); margin-bottom: var(--space-lg); flex-wrap: wrap; }
.summary-card {
  flex: 1; min-width: 120px; background: var(--card); border: 1px solid var(--hairline);
  border-radius: var(--radius-md); padding: var(--space-md); text-align: center;
}
.summary-num { font-size: var(--text-headline); font-weight: 700; color: var(--ink); }
.summary-label { font-size: var(--text-caption); color: var(--ink-muted); margin-top: 4px; }

.trend-stable .summary-num { color: var(--ok); }
.trend-skewed .summary-num { color: var(--warn); }
.trend-danger .summary-num { color: var(--err); }
.balance-greed-heavy .summary-num { color: var(--warn); }
.balance-fear-heavy .summary-num { color: var(--accent); }
.balance-even .summary-num { color: var(--ok); }

.stone-list { display: flex; flex-direction: column; gap: var(--space-sm); }
.stone-row { display: flex; align-items: center; gap: var(--space-sm); }
.stone-rank { width: 28px; font-size: var(--text-caption); color: var(--ink-muted); text-align: right; flex-shrink: 0; }
.stone-name { width: 160px; font-size: var(--text-body); color: var(--ink); flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.stone-bar-wrap { flex: 1; height: 10px; background: var(--hairline); border-radius: 5px; overflow: hidden; }
.stone-bar { height: 100%; background: var(--accent); border-radius: 5px; transition: width 0.3s; }
.stone-count { width: 36px; font-size: var(--text-caption); color: var(--ink-muted); text-align: right; flex-shrink: 0; }

.balance-bar { display: flex; height: 36px; border-radius: var(--radius-sm); overflow: hidden; font-size: var(--text-caption); }
.balance-side { display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 600; transition: flex 0.3s; }
.balance-greed { background: var(--warn); min-width: 60px; }
.balance-fear { background: var(--accent); min-width: 60px; }

.excuse-row { display: flex; gap: var(--space-sm); padding: 6px 0; border-bottom: 1px solid var(--hairline); align-items: center; }
.excuse-row:last-child { border-bottom: none; }
.excuse-index { font-size: var(--text-caption); color: var(--ink-muted); width: 20px; }
.excuse-text { flex: 1; font-size: var(--text-body); color: var(--ink); }
.excuse-count { font-size: var(--text-caption); color: var(--accent); font-weight: 600; }

.timeline-chart { display: flex; gap: 2px; align-items: flex-end; height: 100px; }
.timeline-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; min-width: 0; }
.timeline-bar { width: 100%; max-width: 30px; background: var(--accent); border-radius: 3px 3px 0 0; min-height: 2px; transition: height 0.3s; opacity: 0.8; }
.timeline-bar:hover { opacity: 1; }
.timeline-label { font-size: 9px; color: var(--ink-muted); margin-top: 4px; transform: rotate(-45deg); transform-origin: top left; white-space: nowrap; }
</style>
