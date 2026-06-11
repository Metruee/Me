<template>
  <div style="display:flex;flex-direction:column;height:100%">
    <div class="page-header">
      ← 编辑专家
      <button class="btn btn-ghost accent" style="float:right;font-size:13px;margin-top:-2px;" @click="save">保存</button>
    </div>
    <div class="page-body" style="display:flex;flex-direction:column;gap:var(--space-lg);">

      <div v-if="loading" class="text-center text-muted mt-lg">加载中…</div>

      <template v-else-if="expert">
        <!-- 基本信息 -->
        <div class="settings-group">
          <h3>基本信息</h3>
          <div class="setting-row">
            <span class="label">头像 Emoji</span>
            <input v-model="expert.avatar" style="width:60px;border:1px solid var(--hairline-strong);border-radius:var(--radius-sm);padding:4px 8px;text-align:center;font-size:var(--text-caption);" />
          </div>
          <div class="setting-row">
            <span class="label">名称</span>
            <input v-model="expert.name" style="width:140px;border:1px solid var(--hairline-strong);border-radius:var(--radius-sm);padding:4px 8px;font-size:var(--text-caption);" />
          </div>
          <div class="setting-row">
            <span class="label">领域</span>
            <span class="value">{{ expert.domain }}</span>
          </div>
        </div>

        <!-- 召唤语 / 回应语 -->
        <div class="settings-group">
          <h3>召唤仪式</h3>
          <div class="setting-row" style="flex-direction:column;align-items:stretch;gap:4px;">
            <span class="label">召唤语</span>
            <input v-model="expert.summon_phrase" style="width:100%;border:1px solid var(--hairline-strong);border-radius:var(--radius-sm);padding:8px;font-size:var(--text-body);" placeholder="用户输入此语召唤专家" />
          </div>
          <div class="setting-row" style="flex-direction:column;align-items:stretch;gap:4px;">
            <span class="label">回应语</span>
            <input v-model="expert.response_phrase" style="width:100%;border:1px solid var(--hairline-strong);border-radius:var(--radius-sm);padding:8px;font-size:var(--text-body);" placeholder="专家被召唤时的回应" />
          </div>
        </div>

        <!-- 人格设定 -->
        <div class="settings-group">
          <h3>人格设定 (System Prompt)</h3>
          <textarea
            v-model="expert.system_prompt"
            style="width:100%;min-height:200px;border:1px solid var(--hairline-strong);border-radius:var(--radius-sm);padding:10px;font-family:var(--font-text);font-size:var(--text-caption);line-height:1.5;resize:vertical;"
            placeholder="编辑专家人格设定…"
          ></textarea>
        </div>
      </template>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const expertId = ref(route.params.expertId as string)
const expert = ref<any>(null)
const loading = ref(true)

async function load() {
  try {
    const res = await fetch(`/api/experts/${expertId.value}`)
    if (res.ok) expert.value = await res.json()
  } catch { /* handle error */ }
  loading.value = false
}

async function save() {
  if (!expert.value) return
  try {
    await fetch(`/api/experts/${expertId.value}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(expert.value),
    })
    router.push('/settings')
  } catch { alert('保存失败') }
}

onMounted(load)
</script>
