<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-4px;margin-right:6px">
          <circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>
        设置
      </h2>
    </div>

    <div class="section">
      <n-card title="订阅管理">
        <n-tabs type="line" animated>
          <n-tab-pane name="url" tab="URL导入">
            <n-space vertical :size="12">
              <n-input v-model:value="url" type="textarea" placeholder="请输入订阅URL" :autosize="{ minRows: 2, maxRows: 5 }" />
              <n-button type="primary" :loading="importing" @click="importUrl">导入</n-button>
            </n-space>
          </n-tab-pane>
          <n-tab-pane name="file" tab="文件上传">
            <n-upload :custom-request="onUpload" :show-file-list="false" accept=".json">
              <n-upload-dragger>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity:0.3">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
                <n-text style="font-size:16px">点击或拖拽 JSON 配置文件到此处</n-text>
              </n-upload-dragger>
            </n-upload>
          </n-tab-pane>
        </n-tabs>
      </n-card>
    </div>

    <div class="section">
      <n-card title="配置列表">
        <div v-for="cfg in configs" :key="cfg.id" class="config-item">
          <div class="config-info">
            <span class="config-name">{{ cfg.name }}</span>
            <n-tag v-if="cfg.is_active" size="small" type="success">已激活</n-tag>
          </div>
          <div class="config-actions">
            <n-button v-if="!cfg.is_active" size="small" @click="activate(cfg.id)">激活</n-button>
            <n-button size="small" type="error" ghost @click="remove(cfg.id)">删除</n-button>
          </div>
        </div>
        <div v-if="!configs.length" class="no-config">暂无配置</div>
      </n-card>
    </div>

    <div class="section">
      <n-card title="代理设置">
        <n-space vertical :size="12">
          <n-input v-model:value="proxy" placeholder="http://127.0.0.1:7890 （留空则不使用代理）" />
          <n-button type="primary" @click="saveProxy">保存</n-button>
          <p class="hint">设置后刷新页面生效。用于直播源下载和远程站点访问。</p>
        </n-space>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMessage, NCard, NTabs, NTabPane, NInput, NButton, NUpload, NUploadDragger, NText, NTag, NSpace } from 'naive-ui'
import { importConfig, getConfigs, deleteConfig, activateConfig } from '@/api/config'

const message = useMessage()
const url = ref('')
const importing = ref(false)
const configs = ref<any[]>([])
const proxy = ref('')

onMounted(async () => {
  // Load current proxy
  try {
    const res = await fetch('/api/system/config')
    const data = await res.json()
    proxy.value = data?.data?.proxy || ''
  } catch {}
  await loadConfigs()
})

async function saveProxy() {
  try {
    await fetch('/api/system/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ proxy: proxy.value.trim() }),
    })
    message.success('保存成功，请刷新页面生效')
  } catch (e: any) {
    message.error('保存失败: ' + (e?.message || ''))
  }
}

async function loadConfigs() {
  const res: any = await getConfigs()
  configs.value = res.data || []
}

async function importUrl() {
  if (!url.value.trim()) return message.warning('请输入URL')
  importing.value = true
  try {
    await importConfig({ url: url.value.trim(), type: 'url' })
    message.success('导入成功')
    url.value = ''
    await loadConfigs()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

async function onUpload(options: any) {
  const file = options.file.file as File
  if (!file) return
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      await importConfig({ content: e.target?.result as string, type: 'file' })
      message.success('上传成功')
      await loadConfigs()
      options.onFinish()
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '上传失败')
      options.onError()
    }
  }
  reader.readAsText(file)
}

async function activate(id: number) {
  await activateConfig(id)
  message.success('已激活')
  await loadConfigs()
}

async function remove(id: number) {
  await deleteConfig(id)
  await loadConfigs()
}
</script>

<style scoped>
.settings-page { padding: 20px; max-width: 800px; margin: 0 auto; }
.page-header h2 { margin: 0 0 20px; }
.section { margin-bottom: 20px; }
.config-item { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--n-divider-color); }
.config-item:last-child { border-bottom: none; }
.config-info { display: flex; align-items: center; gap: 8px; }
.config-name { font-size: 14px; }
.config-actions { display: flex; gap: 8px; }
.hint { font-size: 12px; color: #888; margin: 0; }
</style>
