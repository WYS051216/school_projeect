# 职迹 · 面向计算机类应届生的大模型求职能力分析与学习规划平台

产品名「职迹」。这是一个面向计算机类应届毕业生、聚焦初级软件开发岗位求职场景的 Web 平台，
核心闭环为：**材料整理 → 能力证据提炼 → 岗位差距分析 → 简历草拟 → 学习计划**。

> 当前为首期原型，仅实现第一个功能模块「**笔记与材料管理**」。其余功能（大模型能力证据提炼、
> 岗位差距分析、简历草稿、学习计划、OCR、RAG 等）按立项书后续逐步实现。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 + Element Plus + Vite |
| 后端 | Python FastAPI + SQLAlchemy |
| 数据库 | SQLite（默认，零配置；可切换到 MySQL，见下） |
| 大模型 | 大模型 API（后续接入） |

## 目录结构

```
project/
├── backend/           # FastAPI 后端
│   ├── main.py        # 入口 + 路由
│   ├── database.py    # 数据库连接（可切换 MySQL）
│   ├── models.py      # ORM 模型
│   ├── schemas.py     # Pydantic 模型
│   └── requirements.txt
├── frontend/          # Vue 3 前端
│   ├── src/App.vue    # 页面主组件
│   ├── src/api.js     # 接口封装
│   └── ...
└── README.md
```

## 运行步骤

### 1. 启动后端（端口 8000）

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. 启动前端（端口 5173）

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173 即可使用。

## 已实现功能（首期）

- 笔记 / 材料的新建、查看、编辑、删除
- 标题 / 内容全文搜索
- 按类型（笔记 / 材料）与分类筛选
- 标签管理（逗号分隔）
- Markdown 编辑与预览

## 切换 MySQL（可选）

默认使用 SQLite 便于本地直接运行。立项书要求 MySQL，切换方式：

1. 安装驱动：`pip install pymysql`
2. 设置环境变量后再启动后端：

```bash
# Windows (PowerShell)
$env:DATABASE_URL = "mysql+pymysql://用户名:密码@localhost/zhiji?charset=utf8mb4"
uvicorn main:app --reload --port 8000
```

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/notes` | 列表（支持 `type` / `category` / `tag` / `q` 过滤） |
| GET | `/api/notes/{id}` | 详情 |
| POST | `/api/notes` | 新建 |
| PUT | `/api/notes/{id}` | 更新 |
| DELETE | `/api/notes/{id}` | 删除 |
