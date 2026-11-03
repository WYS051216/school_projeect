# 职迹 · 面向计算机类应届生的大模型求职能力分析与学习规划平台

产品名「职迹」。面向计算机类应届毕业生、聚焦初级软件开发岗位求职场景的 Web 平台，
核心闭环为：**材料整理 → 能力证据提炼 → 岗位差距分析 → 简历草拟 → 学习计划**。

> 当前为首期原型，已实现第一个功能模块「**笔记与材料管理**」（多层文件夹树 + 文档 + 整个文件夹上传）。
> 其余功能（大模型能力证据提炼、岗位差距分析、简历草稿、成长路线等）按立项书后续逐步实现。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 + Element Plus + Vite |
| 后端 | Python FastAPI + SQLAlchemy |
| 数据库 | SQLite（默认，零配置；可切换 MySQL） |
| 大模型 | DeepSeek API（预留，待接入） |

## 目录结构

```
project/
├── backend/               # FastAPI 后端
│   ├── main.py            # 入口 + 所有路由
│   ├── database.py        # 数据库连接（可切换 MySQL）
│   ├── models.py          # ORM 模型（Folder / Document）
│   ├── schemas.py         # Pydantic 请求/响应模型
│   ├── requirements.txt   # Python 依赖
│   └── zhiji.db           # SQLite 数据库文件（自动生成，已被 .gitignore 忽略）
├── frontend/              # Vue 3 前端
│   ├── src/App.vue        # 页面主组件
│   ├── src/api.js         # 后端接口封装
│   ├── src/main.js        # 应用入口
│   └── vite.config.js     # Vite 配置（含 /api 代理）
├── .gitignore
└── README.md
```

## 运行步骤

### 1. 启动后端（端口 8000）

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000
```

### 2. 启动前端（端口 5173）

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173 即可使用。

## 已实现功能

- 笔记 / 项目经历两个独立分区（`kind` 字段区分）
- 多层文件夹树（文件夹可套文件夹）
- 上传整个文件夹（自动保持原目录结构）
- 新建 / 重命名 / 删除文件夹与文档
- 右键快捷菜单（类似电脑文件管理器）
- Markdown 编辑与预览
- 文档列表与预览区高度可拖动调整

## 数据存储

所有数据保存在 `backend/zhiji.db`（SQLite 单文件，零配置），共两张表：

- **folders**：文件夹节点。`parent_id` 指向父文件夹（自关联），实现多层嵌套；`kind` 区分「笔记 / 项目经历」。
- **documents**：文档。`folder_id` 关联所属文件夹；正文以纯文本存于 `content`，显示时由前端用 marked 渲染为 Markdown。

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/folders?kind=note` | 列出某分区的文件夹 |
| POST | `/api/folders` | 新建文件夹 |
| PUT | `/api/folders/{id}` | 重命名文件夹 |
| DELETE | `/api/folders/{id}` | 删除文件夹（含子文件夹与文档） |
| GET | `/api/folders/{id}/documents` | 列出某文件夹下的文档 |
| GET | `/api/documents/{id}` | 文档详情 |
| POST | `/api/documents` | 新建文档 |
| PUT | `/api/documents/{id}` | 更新文档 |
| DELETE | `/api/documents/{id}` | 删除文档 |
| POST | `/api/upload-folder` | 上传整个文件夹（保持目录结构） |

## 切换 MySQL（可选）

默认使用 SQLite 便于本地直接运行。立项书要求 MySQL，切换方式：

1. 安装驱动：`pip install pymysql`
2. 设置环境变量后再启动后端：

```bash
# Windows (PowerShell)
$env:DATABASE_URL = "mysql+pymysql://用户名:密码@localhost/zhiji?charset=utf8mb4"
uvicorn main:app --port 8000
```

## 后续计划

- [ ] 大模型能力证据提炼（DeepSeek）
- [ ] 岗位差距分析
- [ ] 简历草拟
- [ ] 成长路线 / 学习计划
