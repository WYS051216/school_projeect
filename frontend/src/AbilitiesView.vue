<template>
  <div class="abilities-view">
    <div class="abilities-toolbar">
      <div class="toolbar-left">
        <span class="title">能力证据</span>
        <el-checkbox
          :model-value="allSelected"
          :indeterminate="someSelected && !allSelected"
          @change="toggleAll"
        >全选</el-checkbox>
      </div>
      <div class="toolbar-right">
        <el-radio-group v-model="filter" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="skill">技能</el-radio-button>
          <el-radio-button label="project">项目</el-radio-button>
          <el-radio-button label="achievement">成果</el-radio-button>
        </el-radio-group>
        <el-button size="small" type="danger" :disabled="!selectedIds.length" @click="batchRemove">
          批量删除{{ selectedIds.length ? `（${selectedIds.length}）` : '' }}
        </el-button>
        <el-button size="small" type="primary" :disabled="!selectedIds.length" @click="openGenerate">
          写进简历{{ selectedIds.length ? `（${selectedIds.length}）` : '' }}
        </el-button>
        <el-button size="small" @click="load">刷新</el-button>
      </div>
    </div>

    <el-empty
      v-if="!filtered.length"
      description="还没有能力证据，去「材料管理」勾选文档后点「AI 抽取能力」"
    />

    <div class="ability-list">
      <div v-for="a in filtered" :key="a.id" class="ability-card">
        <el-checkbox
          class="ability-check"
          :model-value="selectedIds.includes(a.id)"
          @change="toggleSelect(a.id)"
        />
        <el-tag :type="kindTag(a.kind)" size="small" class="kind-tag">{{ kindLabel(a.kind) }}</el-tag>
        <div class="ability-main">
          <div class="ability-name">{{ a.name }}</div>
          <div class="ability-desc">{{ a.description }}</div>
          <div v-if="a.source" class="ability-source">来源：{{ a.source }}</div>
        </div>
        <div class="ability-actions">
          <el-tag v-if="a.confirmed" type="success" size="small">已确认</el-tag>
          <el-button size="small" @click="confirm(a)">{{ a.confirmed ? '取消确认' : '确认' }}</el-button>
          <el-button size="small" @click="edit(a)">编辑</el-button>
          <el-button size="small" type="danger" @click="remove(a)">删除</el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="editVisible" title="编辑能力证据" width="500px">
      <el-form label-width="60px" @submit.prevent>
        <el-form-item label="类型">
          <el-select v-model="editForm.kind" style="width: 100%">
            <el-option label="技能" value="skill" />
            <el-option label="项目" value="project" />
            <el-option label="成果" value="achievement" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="editForm.source" placeholder="可选，如某篇文档标题" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="generateVisible" title="写进简历 · 专业技能栏目" width="640px">
      <el-form label-width="80px" @submit.prevent>
        <el-form-item label="目标岗位">
          <el-input
            v-model="targetPosition"
            placeholder="例如：C++ 后端开发工程师"
            clearable
            @keyup.enter.prevent="doGenerate"
          />
        </el-form-item>
      </el-form>
      <div v-if="generating" class="generate-loading">AI 正在生成，请稍候…</div>
      <template v-if="resumeText">
        <div class="resume-box">
          <div class="resume-text" v-html="resumeHtml"></div>
        </div>
        <div class="resume-actions">
          <el-button size="small" @click="copyResume">复制结果</el-button>
          <el-button size="small" @click="regenerate">重新生成</el-button>
        </div>
      </template>
      <template #footer>
        <el-button @click="generateVisible = false">关闭</el-button>
        <el-button type="primary" :loading="generating" @click="doGenerate">
          {{ resumeText ? '重新生成' : '生成技能栏目' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import {
  batchDeleteAbilities,
  deleteAbility,
  generateResumeSkills,
  listAbilities,
  updateAbility,
} from './api'

const abilities = ref([])
const filter = ref('all')
const selectedIds = ref([])
const editVisible = ref(false)
const editForm = ref({ id: null, kind: 'skill', name: '', description: '', source: '' })
const generateVisible = ref(false)
const targetPosition = ref('')
const resumeText = ref('')
const generating = ref(false)
const resumeHtml = computed(() => marked.parse(resumeText.value || '', { breaks: true }))

const filtered = computed(() =>
  filter.value === 'all' ? abilities.value : abilities.value.filter((a) => a.kind === filter.value),
)

const allSelected = computed(() => {
  const ids = filtered.value.map((a) => a.id)
  return ids.length > 0 && ids.every((id) => selectedIds.value.includes(id))
})

const someSelected = computed(() => filtered.value.some((a) => selectedIds.value.includes(a.id)))

function kindLabel(kind) {
  return { skill: '技能', project: '项目', achievement: '成果' }[kind] || kind
}
function kindTag(kind) {
  return { skill: '', project: 'warning', achievement: 'success' }[kind] || ''
}

async function load() {
  try {
    abilities.value = await listAbilities()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function toggleSelect(id) {
  const i = selectedIds.value.indexOf(id)
  if (i >= 0) selectedIds.value.splice(i, 1)
  else selectedIds.value.push(id)
}

function toggleAll(val) {
  const ids = filtered.value.map((a) => a.id)
  if (val) {
    const set = new Set(selectedIds.value)
    ids.forEach((id) => set.add(id))
    selectedIds.value = Array.from(set)
  } else {
    selectedIds.value = selectedIds.value.filter((id) => !ids.includes(id))
  }
}

async function batchRemove() {
  if (!selectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`删除选中的 ${selectedIds.value.length} 条能力？`, '批量删除', { type: 'warning' })
  } catch {
    return
  }
  try {
    await batchDeleteAbilities(selectedIds.value)
    ElMessage.success('已删除')
    selectedIds.value = []
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function confirm(a) {
  try {
    await updateAbility(a.id, { confirmed: !a.confirmed })
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function edit(a) {
  editForm.value = {
    id: a.id,
    kind: a.kind,
    name: a.name,
    description: a.description,
    source: a.source || '',
  }
  editVisible.value = true
}

async function saveEdit() {
  try {
    await updateAbility(editForm.value.id, {
      kind: editForm.value.kind,
      name: editForm.value.name,
      description: editForm.value.description,
      source: editForm.value.source,
    })
    ElMessage.success('已保存')
    editVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function remove(a) {
  try {
    await ElMessageBox.confirm(`删除能力「${a.name}」？`, '确认', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteAbility(a.id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function openGenerate() {
  resumeText.value = ''
  generateVisible.value = true
}

async function doGenerate() {
  if (!targetPosition.value.trim()) {
    ElMessage.warning('请先填写目标岗位')
    return
  }
  generating.value = true
  try {
    const res = await generateResumeSkills(selectedIds.value, targetPosition.value.trim())
    resumeText.value = res.content
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    generating.value = false
  }
}

async function regenerate() {
  resumeText.value = ''
  await doGenerate()
}

async function copyResume() {
  try {
    await navigator.clipboard.writeText(resumeText.value)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动选中文本复制')
  }
}

onMounted(load)
</script>

<style scoped>
.abilities-view {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 16px 20px;
}
.abilities-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.ability-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ability-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px 16px;
}
.ability-check {
  flex-shrink: 0;
  margin-top: 2px;
}
.kind-tag {
  flex-shrink: 0;
  margin-top: 2px;
}
.ability-main {
  flex: 1;
  min-width: 0;
}
.ability-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.ability-desc {
  font-size: 13px;
  color: #606266;
  margin-top: 4px;
  line-height: 1.6;
}
.ability-source {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}
.ability-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.generate-loading {
  padding: 16px;
  color: #409eff;
  text-align: center;
}
.resume-box {
  max-height: 360px;
  overflow-y: auto;
  background: #f7f8fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px 14px;
  margin-bottom: 10px;
}
.resume-text {
  margin: 0;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.7;
  color: #303133;
}
.resume-text :deep(p) {
  margin: 0 0 6px;
}
.resume-text :deep(strong) {
  color: #303133;
}
.resume-actions {
  display: flex;
  gap: 10px;
}
</style>
