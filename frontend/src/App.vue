<template>
  <div class="app">
    <header class="app-header">
      <div class="brand">
        <span class="logo">职迹</span>
      </div>
      <div class="nav">
        <el-button :type="view === 'materials' ? 'primary' : 'default'" size="small" @click="view = 'materials'">材料管理</el-button>
        <el-button :type="view === 'abilities' ? 'primary' : 'default'" size="small" @click="view = 'abilities'">能力证据</el-button>
      </div>
    </header>

    <AbilitiesView v-if="view === 'abilities'" />

    <div v-else class="layout">
      <aside class="sidebar">
        <el-tabs v-model="kind" class="kind-tabs">
          <el-tab-pane label="笔记" name="note" />
          <el-tab-pane label="项目经历" name="project" />
        </el-tabs>

        <div class="sidebar-tools">
          <el-button type="primary" style="width: 100%" @click="pickFolder">＋ 上传文件夹</el-button>
          <el-button style="width: 100%" @click="newFolder">＋ 新建文件夹</el-button>
          <input ref="folderInput" type="file" webkitdirectory style="display: none" @change="onFolderPicked" />
        </div>

        <div class="tree-wrap">
          <el-tree
            :key="treeVersion"
            :data="tree"
            :props="{ label: 'name', children: 'children' }"
            node-key="id"
            highlight-current
            default-expand-all
            :expand-on-click-node="false"
            @node-click="onFolderClick"
          >
            <template #default="{ node, data }">
              <span class="tree-node" @contextmenu.prevent="onFolderContextMenu($event, data)">
                <span class="tree-node-label">{{ node.label }}</span>
              </span>
            </template>
          </el-tree>
          <el-empty v-if="!tree.length" description="还没有文件夹，先上传或新建" :image-size="60" />
        </div>
      </aside>

      <main class="content" ref="contentRef">
        <section class="doc-list" :style="{ height: docListHeight + 'px' }">
          <div class="doc-list-header">
            <span class="cur-folder">{{ currentFolder ? currentFolder.name : '请选择左侧文件夹' }}</span>
            <div class="doc-list-actions">
              <el-button size="small" type="primary" :disabled="!selectedDocIds.length" :loading="extracting" @click="extractSelected">
                AI 抽取能力{{ selectedDocIds.length ? `（已选 ${selectedDocIds.length}）` : '' }}
              </el-button>
              <el-button size="small" @click="newDoc">＋ 新建文档</el-button>
            </div>
          </div>
          <div class="doc-list-selectbar">
            <el-checkbox
              :model-value="allSelected"
              :indeterminate="someSelected && !allSelected"
              @change="toggleAll"
            >
              全选当前文件夹
            </el-checkbox>
            <span class="selected-count">已选 {{ selectedDocIds.length }} 篇</span>
          </div>
          <div
            v-for="d in documents"
            :key="d.id"
            class="doc-item"
            :class="{ active: currentDoc && currentDoc.id === d.id }"
            @contextmenu.prevent="onDocContextMenu($event, d)"
          >
            <el-checkbox
              :model-value="selectedDocIds.includes(d.id)"
              @change="toggleSelect(d.id)"
              @click.stop
            />
            <span class="doc-name" @click="openDoc(d)">{{ d.title }}</span>
          </div>
          <el-empty
            v-if="!documents.length"
            :description="currentFolder ? '该文件夹下暂无文档' : '请在左侧选择文件夹'"
            :image-size="50"
          />
        </section>

        <div class="resizer" @mousedown="startResize"></div>

        <section class="doc-viewer">
          <template v-if="currentDoc">
            <div class="doc-viewer-toolbar">
              <el-input v-model="docTitle" style="width: 320px" />
              <el-button-group>
                <el-button :type="mode === 'preview' ? 'primary' : 'default'" @click="mode = 'preview'">预览</el-button>
                <el-button :type="mode === 'edit' ? 'primary' : 'default'" @click="mode = 'edit'">编辑</el-button>
              </el-button-group>
              <el-button type="primary" :loading="saving" @click="saveDoc">保存</el-button>
            </div>
            <div class="doc-viewer-body">
              <el-input
                v-show="mode === 'edit'"
                v-model="docContent"
                type="textarea"
                class="md-input"
                resize="none"
              />
              <div v-show="mode === 'preview'" class="md-preview" v-html="rendered"></div>
            </div>
          </template>
          <el-empty v-else description="点击左侧文档查看内容" style="margin-top: 120px" />
        </section>
      </main>
    </div>
  </div>

  <teleport to="body">
    <div ref="menuRef" v-if="menu.visible" class="ctx-menu" :style="{ left: menu.x + 'px', top: menu.y + 'px' }">
      <div
        v-for="(item, i) in menu.items"
        :key="i"
        class="ctx-item"
        :class="{ danger: item.danger }"
        @click="runMenuAction(item)"
      >
        {{ item.label }}
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import AbilitiesView from './AbilitiesView.vue'
import {
  createDocument,
  createFolder,
  deleteDocument,
  deleteFolder,
  extractAbilities,
  extractFolderAbilities,
  getDocument,
  listDocuments,
  listFolders,
  renameFolder as renameFolderApi,
  updateDocument,
  uploadFolder,
} from './api'

const kind = ref('note')
const folders = ref([])
const treeVersion = ref(0)
const currentFolder = ref(null)
const documents = ref([])
const currentDoc = ref(null)
const docTitle = ref('')
const docContent = ref('')
const mode = ref('preview')
const saving = ref(false)
const folderInput = ref(null)
const contentRef = ref(null)
const docListHeight = ref(280)
const menu = ref({ visible: false, x: 0, y: 0, items: [], target: null })
const menuRef = ref(null)
const view = ref('materials')
const selectedDocIds = ref([])
const extracting = ref(false)

const tree = computed(() => buildTree(folders.value))
const rendered = computed(() => marked.parse(docContent.value || ''))

function buildTree(list) {
  const map = {}
  const roots = []
  list.forEach((f) => {
    map[f.id] = { ...f, children: [] }
  })
  list.forEach((f) => {
    const node = map[f.id]
    if (f.parent_id && map[f.parent_id]) map[f.parent_id].children.push(node)
    else roots.push(node)
  })
  return roots
}

async function loadFolders() {
  try {
    folders.value = await listFolders(kind.value)
    treeVersion.value++
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function loadDocuments(folderId) {
  documents.value = await listDocuments(folderId)
}

function onFolderClick(data) {
  currentFolder.value = data
  currentDoc.value = null
  loadDocuments(data.id)
}

async function openDoc(d) {
  const full = await getDocument(d.id)
  currentDoc.value = full
  docTitle.value = full.title
  docContent.value = full.content
  mode.value = 'preview'
}

const allSelected = computed(() => {
  const ids = documents.value.map((d) => d.id)
  return ids.length > 0 && ids.every((id) => selectedDocIds.value.includes(id))
})

const someSelected = computed(() =>
  documents.value.some((d) => selectedDocIds.value.includes(d.id)),
)

function toggleAll(val) {
  const ids = documents.value.map((d) => d.id)
  if (val) {
    const set = new Set(selectedDocIds.value)
    ids.forEach((id) => set.add(id))
    selectedDocIds.value = Array.from(set)
  } else {
    selectedDocIds.value = selectedDocIds.value.filter((id) => !ids.includes(id))
  }
}

function toggleSelect(id) {
  const i = selectedDocIds.value.indexOf(id)
  if (i >= 0) selectedDocIds.value.splice(i, 1)
  else selectedDocIds.value.push(id)
}

async function extractSelected() {
  if (!selectedDocIds.value.length) return
  extracting.value = true
  try {
    const result = await extractAbilities(selectedDocIds.value)
    ElMessage.success(`抽取成功，新增 ${result.length} 条能力证据`)
    selectedDocIds.value = []
    view.value = 'abilities'
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    extracting.value = false
  }
}

async function extractFolder(folder) {
  extracting.value = true
  try {
    const result = await extractFolderAbilities(folder.id)
    ElMessage.success(`抽取成功，新增 ${result.length} 条能力证据`)
    view.value = 'abilities'
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    extracting.value = false
  }
}

function pickFolder() {
  folderInput.value.click()
}

async function onFolderPicked(e) {
  const files = Array.from(e.target.files || [])
  e.target.value = ''
  const mdFiles = files.filter((f) => /\.(md|txt|markdown)$/i.test(f.name))
  if (!mdFiles.length) {
    ElMessage.warning('该文件夹里没有 .md 或 .txt 文件')
    return
  }
  const items = []
  for (const f of mdFiles) {
    const content = await f.text()
    items.push({ path: f.webkitRelativePath || f.name, content })
  }
  try {
    const r = await uploadFolder(kind.value, items)
    ElMessage.success(`上传成功：新增 ${r.folders_created} 个文件夹、${r.documents_created} 篇文档`)
    await loadFolders()
    const top = items[0].path.split('/')[0]
    const found = folders.value.find((f) => f.name === top && !f.parent_id)
    if (found) onFolderClick(found)
  } catch (err) {
    ElMessage.error(err.message)
  }
}

function newFolder() {
  promptNewFolder(currentFolder.value)
}

function newDoc() {
  if (!currentFolder.value) {
    ElMessage.warning('请先在左侧选择一个文件夹')
    return
  }
  promptNewDoc(currentFolder.value)
}

function promptNewFolder(parent) {
  ElMessageBox.prompt('输入文件夹名称', '新建文件夹', { inputValue: '' })
    .then(async ({ value }) => {
      await createFolder({ name: value, parent_id: parent ? parent.id : null, kind: kind.value })
      ElMessage.success('已创建')
      await loadFolders()
    })
    .catch(() => {})
}

function promptNewDoc(parent) {
  ElMessageBox.prompt('输入文档名称（如 xxx.md）', '新建文档', { inputValue: '' })
    .then(async ({ value }) => {
      const doc = await createDocument({ folder_id: parent.id, title: value, content: '', tags: [] })
      ElMessage.success('已创建')
      await loadDocuments(parent.id)
      await openDoc(doc)
    })
    .catch(() => {})
}

async function saveDoc() {
  if (!currentDoc.value) return
  saving.value = true
  try {
    await updateDocument(currentDoc.value.id, { title: docTitle.value, content: docContent.value })
    ElMessage.success('已保存')
    await loadDocuments(currentFolder.value.id)
  } catch (err) {
    ElMessage.error(err.message)
  } finally {
    saving.value = false
  }
}

async function removeDoc(d) {
  try {
    await ElMessageBox.confirm(`删除文档「${d.title}」？`, '确认', { type: 'warning' })
  } catch {
    return
  }
  await deleteDocument(d.id)
  ElMessage.success('已删除')
  if (currentDoc.value && currentDoc.value.id === d.id) currentDoc.value = null
  await loadDocuments(currentFolder.value.id)
}

async function removeFolder(data) {
  try {
    await ElMessageBox.confirm(`删除文件夹「${data.name}」及其下所有子文件夹和文档？`, '确认删除', { type: 'warning' })
  } catch {
    return
  }
  await deleteFolder(data.id)
  ElMessage.success('已删除')
  if (currentFolder.value && currentFolder.value.id === data.id) {
    currentFolder.value = null
    currentDoc.value = null
    documents.value = []
  }
  await loadFolders()
}

function renameFolder(folder) {
  ElMessageBox.prompt('输入新的文件夹名称', '重命名', { inputValue: folder.name })
    .then(async ({ value }) => {
      await renameFolderApi(folder.id, value)
      if (currentFolder.value && currentFolder.value.id === folder.id) {
        currentFolder.value.name = value
      }
      ElMessage.success('已重命名')
      await loadFolders()
    })
    .catch(() => {})
}

function renameDoc(doc) {
  ElMessageBox.prompt('输入新的文档名称', '重命名', { inputValue: doc.title })
    .then(async ({ value }) => {
      await updateDocument(doc.id, { title: value })
      ElMessage.success('已重命名')
      await loadDocuments(currentFolder.value.id)
    })
    .catch(() => {})
}

async function showMenu(e, items, target) {
  menu.value = { visible: true, x: e.clientX, y: e.clientY, items, target }
  await nextTick()
  const el = menuRef.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  let x = e.clientX
  let y = e.clientY
  // 超出屏幕右边界或底部时，翻转方向，保证菜单完整可见
  if (x + rect.width > window.innerWidth) x = Math.max(0, window.innerWidth - rect.width - 8)
  if (y + rect.height > window.innerHeight) y = Math.max(0, y - rect.height)
  menu.value.x = x
  menu.value.y = y
}

function onFolderContextMenu(e, data) {
  showMenu(
    e,
    [
      { label: '重命名', action: 'renameFolder' },
      { label: '新建子文件夹', action: 'newSubFolder' },
      { label: '新建文档', action: 'newDocInFolder' },
      { label: 'AI 抽取能力', action: 'extractFolder' },
      { label: '删除文件夹', action: 'deleteFolder', danger: true },
    ],
    data,
  )
}

function onDocContextMenu(e, d) {
  showMenu(
    e,
    [
      { label: '重命名', action: 'renameDoc' },
      { label: '删除文档', action: 'deleteDoc', danger: true },
    ],
    d,
  )
}

function closeMenu() {
  menu.value.visible = false
}

function runMenuAction(item) {
  const t = menu.value.target
  closeMenu()
  if (item.action === 'newSubFolder') promptNewFolder(t)
  else if (item.action === 'newDocInFolder') promptNewDoc(t)
  else if (item.action === 'extractFolder') extractFolder(t)
  else if (item.action === 'deleteFolder') removeFolder(t)
  else if (item.action === 'deleteDoc') removeDoc(t)
  else if (item.action === 'renameFolder') renameFolder(t)
  else if (item.action === 'renameDoc') renameDoc(t)
}

function startResize(e) {
  const startY = e.clientY
  const startH = docListHeight.value
  const contentH = contentRef.value ? contentRef.value.clientHeight : 600
  const maxH = Math.max(contentH - 140, 120)
  const onMove = (ev) => {
    const newH = startH + (ev.clientY - startY)
    docListHeight.value = Math.min(Math.max(newH, 100), maxH)
  }
  const onUp = () => {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

watch(kind, () => {
  currentFolder.value = null
  currentDoc.value = null
  documents.value = []
  loadFolders()
})

onMounted(() => {
  loadFolders()
  document.addEventListener('click', closeMenu)
})
</script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
}
body {
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f5f7fa;
}
.ctx-menu {
  position: fixed;
  z-index: 3000;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  padding: 4px 0;
  min-width: 140px;
}
.ctx-item {
  padding: 8px 16px;
  font-size: 13px;
  color: #303133;
  cursor: pointer;
}
.ctx-item:hover {
  background: #f5f7fa;
}
.ctx-item.danger {
  color: #f56c6c;
}
</style>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.brand {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.logo {
  font-size: 22px;
  font-weight: 700;
  color: #409eff;
}
.nav {
  display: flex;
  gap: 8px;
}

.layout {
  flex: 1;
  display: flex;
  min-height: 0;
}

.sidebar {
  width: 280px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}
.kind-tabs {
  padding: 0 12px;
}
.sidebar-tools {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-bottom: 1px solid #ebeef5;
}
.tree-wrap {
  flex: 1;
  overflow-y: auto;
  padding: 8px 6px;
}
.tree-node {
  display: flex;
  align-items: center;
  width: 100%;
  padding-right: 4px;
}
.tree-node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 16px;
}

.doc-list {
  flex-shrink: 0;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow-y: auto;
  padding: 12px;
}
.doc-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.cur-folder {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.doc-list-actions {
  display: flex;
  gap: 8px;
}
.doc-list-selectbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.selected-count {
  font-size: 12px;
  color: #909399;
}
.doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
}
.doc-item:hover {
  background: #f5f7fa;
}
.doc-item.active {
  background: #ecf5ff;
}
.doc-name {
  flex: 1;
  font-size: 14px;
  color: #303133;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.resizer {
  height: 12px;
  flex-shrink: 0;
  cursor: row-resize;
  display: flex;
  align-items: center;
  justify-content: center;
}
.resizer::before {
  content: '';
  width: 48px;
  height: 3px;
  border-radius: 2px;
  background: #dcdfe6;
}
.resizer:hover::before {
  background: #409eff;
}

.doc-viewer {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
}
.doc-viewer-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid #ebeef5;
}
.doc-viewer-body {
  flex: 1;
  min-height: 0;
}
.md-input {
  height: 100%;
}
.md-input :deep(.el-textarea__inner) {
  height: 100%;
  min-height: 100%;
  border: none;
  box-shadow: none;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
  font-size: 14px;
  line-height: 1.7;
}
.md-preview {
  height: 100%;
  overflow-y: auto;
  padding: 20px 28px;
  line-height: 1.7;
  color: #303133;
}
</style>
