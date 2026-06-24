<template>
  <div style="display:flex;flex-direction:column;height:100%">
    <div class="page-header">设置</div>
    <div class="page-body" style="display:flex;flex-direction:column;gap:var(--space-lg);padding-bottom:calc(var(--space-3xl) + var(--safe-bottom));">

      <!-- API 配置 -->
      <div class="settings-group">
        <h3 class="section-toggle" @click="toggleSection('api')">
          <span>API 配置</span>
          <span class="toggle-icon">{{ sections.api ? '▾' : '▸' }}</span>
        </h3>
        <template v-if="sections.api">
          <div class="setting-row" style="flex-direction:column;align-items:stretch;gap:4px;">
            <span class="label">LLM 接口</span>
            <div style="display:flex;gap:8px;">
              <input v-model="editableConfig.llm_api_base" style="flex:1;border:1px solid var(--hairline-strong);border-radius:var(--radius-sm);padding:6px 10px;font-size:var(--text-caption);min-width:0;" placeholder="例如: http://192.168.0.188:1234/v1" />
              <button class="btn btn-primary" style="height:32px;font-size:12px;padding:0 12px;white-space:nowrap;flex-shrink:0;" @click="saveAndFetchModels">保存并拉取</button>
            </div>
            <div v-if="editableConfig.llm_api_base && config.llm_api_base === editableConfig.llm_api_base" class="text-fine" style="color:var(--accent);">✓ 已保存</div>
          </div>
          <div class="setting-row" style="flex-direction:column;align-items:stretch;gap:4px;">
            <span class="label">LLM 模型</span>
            <div style="display:flex;gap:8px;">
              <select v-model="editableConfig.llm_model" style="flex:1;min-width:0;border:1px solid var(--hairline-strong);border-radius:var(--radius-sm);padding:6px 10px;font-size:var(--text-caption);background:var(--surface-1);" :style="editableConfig.llm_model ? 'border-color:var(--accent);background:var(--accent-soft);' : ''">
                <option value="" disabled>请选择模型…</option>
                <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
              </select>
              <button class="btn btn-primary" style="height:32px;font-size:12px;padding:0 12px;white-space:nowrap;flex-shrink:0;" @click="saveConfig">保存</button>
            </div>
            <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
              <button class="btn btn-ghost" style="height:28px;font-size:11px;padding:0 8px;" @click="fetchModels" :disabled="modelsLoading">
                {{ modelsLoading ? '⏳ 拉取中…' : '🔄 刷新模型列表' }}
              </button>
              <span v-if="availableModels.length" class="text-fine" style="color:var(--ink-muted);">{{ availableModels.length }} 个可用</span>
            </div>
            <div v-if="editableConfig.llm_model && config.llm_model === editableConfig.llm_model" class="text-fine" style="color:var(--accent);">✓ 已保存: {{ editableConfig.llm_model }}</div>
            <div v-else-if="editableConfig.llm_model && config.llm_model !== editableConfig.llm_model" class="text-fine" style="color:var(--warning);">未保存</div>
            <div v-if="modelsError" class="text-fine" style="color:var(--danger);">{{ modelsError }}</div>
          </div>
          <div class="setting-row" style="flex-direction:column;align-items:stretch;gap:4px;">
            <span class="label">Embedding 服务</span>
            <div style="display:flex;gap:8px;">
              <input v-model="editableConfig.embedding_api_base" style="flex:1;min-width:0;border:1px solid var(--hairline-strong);border-radius:var(--radius-sm);padding:6px 10px;font-size:var(--text-caption);" placeholder="与 LLM 接口相同" />
              <button class="btn btn-primary" style="height:32px;font-size:12px;padding:0 12px;white-space:nowrap;flex-shrink:0;" @click="saveAndFetchModels">保存并拉取</button>
            </div>
            <div v-if="editableConfig.embedding_api_base && config.embedding_api_base === editableConfig.embedding_api_base" class="text-fine" style="color:var(--accent);">✓ 已保存: {{ editableConfig.embedding_api_base }}</div>
            <div v-else-if="editableConfig.embedding_api_base && config.embedding_api_base !== editableConfig.embedding_api_base" class="text-fine" style="color:var(--warning);">未保存</div>
          </div>
          <div class="setting-row" style="flex-direction:column;align-items:stretch;gap:4px;">
            <span class="label">Embedding 模型</span>
            <div style="display:flex;gap:8px;">
              <select v-model="editableConfig.embedding_model" style="flex:1;min-width:0;border:1px solid var(--hairline-strong);border-radius:var(--radius-sm);padding:6px 10px;font-size:var(--text-caption);background:var(--surface-1);" :style="editableConfig.embedding_model ? 'border-color:var(--accent);background:var(--accent-soft);' : ''">
                <option value="" disabled>请选择 embedding 模型…</option>
                <option v-for="m in embeddingModels" :key="m" :value="m">{{ m }}</option>
              </select>
              <button class="btn btn-primary" style="height:32px;font-size:12px;padding:0 12px;white-space:nowrap;flex-shrink:0;" @click="saveConfig">保存</button>
            </div>
            <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
              <button class="btn btn-ghost" style="height:28px;font-size:11px;padding:0 8px;" @click="fetchModels" :disabled="modelsLoading">
                {{ modelsLoading ? '⏳ 拉取中…' : '🔄 刷新模型列表' }}
              </button>
              <span v-if="embeddingModels.length" class="text-fine" style="color:var(--ink-muted);">{{ embeddingModels.length }} 个可用</span>
            </div>
            <div v-if="editableConfig.embedding_model && config.embedding_model === editableConfig.embedding_model" class="text-fine" style="color:var(--accent);">✓ 已保存: {{ editableConfig.embedding_model }}</div>
            <div v-else-if="editableConfig.embedding_model && config.embedding_model !== editableConfig.embedding_model" class="text-fine" style="color:var(--warning);">未保存</div>
          </div>
        </template>
      </div>

      <!-- 知识库 -->
      <div class="settings-group">
        <h3 class="section-toggle" @click="toggleSection('knowledge')">
          <span>知识库</span>
          <span class="toggle-icon">{{ sections.knowledge ? '▾' : '▸' }}</span>
        </h3>
        <template v-if="sections.knowledge">
          <div class="setting-row">
            <span class="label">自动归档</span>
            <button class="btn btn-ghost" style="height:30px;font-size:12px;padding:0 10px;" @click="toggleAutoArchive">{{ config.auto_archive === 'true' ? '已开启' : '已关闭' }}</button>
          </div>
          <div class="setting-row" style="flex-direction:column;align-items:stretch;gap:4px;">
            <span class="label">语义相似度阈值</span>
            <div style="display:flex;gap:8px;">
              <input v-model="editableConfig.similarity_threshold" type="number" step="0.05" min="0" max="1" style="width:80px;border:1px solid var(--hairline-strong);border-radius:var(--radius-sm);padding:6px 10px;font-size:var(--text-caption);" />
              <button class="btn btn-primary" style="height:32px;font-size:12px;padding:0 10px;" @click="saveConfig">保存</button>
            </div>
          </div>
          <div class="setting-row" style="flex-direction:column;align-items:stretch;gap:4px;">
            <span class="label">对话历史轮数</span>
            <div style="display:flex;gap:8px;">
              <input v-model="editableConfig.chat_history_rounds" type="number" step="1" min="0" max="50" style="width:80px;border:1px solid var(--hairline-strong);border-radius:var(--radius-sm);padding:6px 10px;font-size:var(--text-caption);" />
              <button class="btn btn-primary" style="height:32px;font-size:12px;padding:0 10px;" @click="saveConfig">保存</button>
            </div>
          </div>
        </template>
      </div>

      <!-- 数据管理 -->
      <div class="settings-group">
        <h3 class="section-toggle" @click="toggleSection('data')">
          <span>数据管理</span>
          <span class="toggle-icon">{{ sections.data ? '▾' : '▸' }}</span>
        </h3>
        <template v-if="sections.data">
          <div class="setting-row">
            <span class="label">导出全部数据</span>
            <button class="btn btn-primary" style="height:34px;font-size:13px;padding:0 14px;" @click="exportData">导出</button>
          </div>
          <div class="setting-row">
            <span class="label">清空知识库</span>
            <button class="btn btn-danger" @click="confirmClear">清空</button>
          </div>
        </template>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, watch } from 'vue'

const config = ref<Record<string,string>>({})
const editableConfig = reactive<Record<string,string>>({
  llm_api_base: '',
  llm_model: '',
  embedding_api_base: '',
  embedding_model: '',
  similarity_threshold: '0.6',
  chat_history_rounds: '10',
})
const availableModels = ref<string[]>([])
const embeddingModels = ref<string[]>([])
const modelsLoading = ref(false)
const modelsError = ref('')
// 手风琴折叠状态（API 默认展开，其余默认收起）
const sections = reactive<Record<string,boolean>>({
  api: true,
  knowledge: false,
  data: false,
})

function toggleSection(key: string) {
  sections[key] = !sections[key]
}

// 同步 config 到 editableConfig
watch(config, (c) => {
  editableConfig.llm_api_base = c.llm_api_base || ''
  editableConfig.llm_model = c.llm_model || ''
  editableConfig.embedding_api_base = c.embedding_api_base || ''
  editableConfig.embedding_model = c.embedding_model || ''
  editableConfig.similarity_threshold = c.similarity_threshold || '0.6'
  editableConfig.chat_history_rounds = c.chat_history_rounds || '10'
}, { immediate: true, deep: true })

async function fetchAll() {
  try {
    const cfgRes = await fetch('/api/config')
    if (cfgRes.ok) config.value = await cfgRes.json()
  } catch { /* use defaults */ }
  fetchModels()
}

async function saveConfig() {
  try {
    const res = await fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editableConfig),
    })
    if (res.ok) {
      // 后端只返回 {"ok":true}，不含配置内容，直接信任前端 edits
      config.value = { ...editableConfig }
    }
  } catch { /* ignore */ }
}

async function saveAndFetchModels() {
  await saveConfig()
  await fetchModels()
}

async function toggleAutoArchive() {
  const newVal = config.value.auto_archive === 'true' ? 'false' : 'true'
  try {
    await fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ auto_archive: newVal }),
    })
    config.value.auto_archive = newVal
  } catch { /* ignore */ }
}

function exportData() { window.open('/api/export', '_blank') }
function confirmClear() {
  if (window.confirm('确定清空知识库？此操作不可撤销。')) {
    fetch('/api/knowledge/clear', { method: 'DELETE' }).then(() => alert('知识库已清空'))
  }
}

async function fetchModels() {
  modelsLoading.value = true
  modelsError.value = ''
  try {
    const res = await fetch('/api/models?include_embedding=true')
    const data = await res.json()
    if (data.ok) {
      availableModels.value = data.models || []
      embeddingModels.value = data.embedding_models || []
      if (!data.models?.length && !data.embedding_models?.length && data.error) {
        modelsError.value = data.error
      }
    }
  } catch {
    modelsError.value = '无法获取模型列表'
  }
  modelsLoading.value = false
}

onMounted(() => { fetchAll(); fetchModels() })
</script>

<style scoped>
.section-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}
.toggle-icon {
  font-size: 14px;
  color: var(--ink-muted);
  transition: transform 0.15s var(--ease-out);
}
</style>
