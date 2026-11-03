// 后端接口封装
const BASE = '/api'

async function request(url, options = {}) {
  const res = await fetch(BASE + url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new Error(data?.detail || '请求失败')
  return data
}

// 文件夹
export const listFolders = (kind = 'note') => request(`/folders?kind=${kind}`)
export const createFolder = (data) =>
  request('/folders', { method: 'POST', body: JSON.stringify(data) })
export const deleteFolder = (id) => request(`/folders/${id}`, { method: 'DELETE' })
export const renameFolder = (id, name) =>
  request(`/folders/${id}`, { method: 'PUT', body: JSON.stringify({ name }) })

// 文档
export const listDocuments = (folderId) => request(`/folders/${folderId}/documents`)
export const getDocument = (id) => request(`/documents/${id}`)
export const createDocument = (data) =>
  request('/documents', { method: 'POST', body: JSON.stringify(data) })
export const updateDocument = (id, data) =>
  request(`/documents/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteDocument = (id) => request(`/documents/${id}`, { method: 'DELETE' })

// 上传整个文件夹（kind + 文件列表[{path, content}]）
export const uploadFolder = (kind, files) =>
  request('/upload-folder', { method: 'POST', body: JSON.stringify({ kind, files }) })

// 能力证据
export const listAbilities = () => request('/abilities')
export const extractAbilities = (documentIds) =>
  request('/extract-abilities', { method: 'POST', body: JSON.stringify({ document_ids: documentIds }) })
export const extractFolderAbilities = (folderId) =>
  request('/extract-folder', { method: 'POST', body: JSON.stringify({ folder_id: folderId }) })
export const updateAbility = (id, data) =>
  request(`/abilities/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteAbility = (id) => request(`/abilities/${id}`, { method: 'DELETE' })
export const batchDeleteAbilities = (ids) =>
  request('/abilities/batch-delete', { method: 'POST', body: JSON.stringify({ ids }) })
export const generateResumeSkills = (abilityIds, targetPosition) =>
  request('/generate-resume-skills', {
    method: 'POST',
    body: JSON.stringify({ ability_ids: abilityIds, target_position: targetPosition }),
  })
