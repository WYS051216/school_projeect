"""职迹 · 后端入口（FastAPI）。

核心功能：文件夹树（笔记 / 项目经历两个区）+ 文档 + 整个文件夹上传（保持目录结构）。
"""
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine, get_db
from models import Document, Folder
from schemas import (
    DocumentCreate,
    DocumentOut,
    DocumentUpdate,
    FolderCreate,
    FolderOut,
    FolderUpdate,
    UploadFolderRequest,
)

Base.metadata.create_all(bind=engine)


def _seed(db: Session) -> None:
    """首次启动写入一个示例文件夹 + 一篇示例文档，便于理解结构。"""
    if db.query(Folder).count() > 0:
        return
    folder = Folder(name="示例笔记", parent_id=None, kind="note")
    db.add(folder)
    db.flush()
    db.add(
        Document(
            folder_id=folder.id,
            title="欢迎.md",
            content="""# 欢迎使用职迹

把本地文件夹上传到左侧，你的 Markdown 笔记会按原目录结构归纳好。

之后 AI 会读取这些归纳好的笔记，分析你的能力与目标岗位的差距，并给出成长路线。
""",
        )
    )
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        _seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title="职迹 · 求职能力分析与学习规划平台", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "zhiji-backend"}


# ---------- 文件夹 ----------
@app.get("/api/folders", response_model=List[FolderOut])
def list_folders(kind: str = "note", db: Session = Depends(get_db)):
    return db.query(Folder).filter(Folder.kind == kind).order_by(Folder.id).all()


@app.post("/api/folders", response_model=FolderOut, status_code=201)
def create_folder(payload: FolderCreate, db: Session = Depends(get_db)):
    folder = Folder(**payload.model_dump())
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@app.put("/api/folders/{folder_id}", response_model=FolderOut)
def update_folder(folder_id: int, payload: FolderUpdate, db: Session = Depends(get_db)):
    folder = db.get(Folder, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    folder.name = payload.name
    db.commit()
    db.refresh(folder)
    return folder


def _delete_folder_recursive(db: Session, folder: Folder) -> None:
    children = db.query(Folder).filter(Folder.parent_id == folder.id).all()
    for child in children:
        _delete_folder_recursive(db, child)
    db.query(Document).filter(Document.folder_id == folder.id).delete()
    db.delete(folder)


@app.delete("/api/folders/{folder_id}", status_code=204)
def delete_folder(folder_id: int, db: Session = Depends(get_db)):
    folder = db.get(Folder, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    _delete_folder_recursive(db, folder)
    db.commit()
    return None


# ---------- 文档 ----------
@app.get("/api/folders/{folder_id}/documents", response_model=List[DocumentOut])
def list_documents(folder_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Document)
        .filter(Document.folder_id == folder_id)
        .order_by(Document.title)
        .all()
    )


@app.get("/api/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc


@app.post("/api/documents", response_model=DocumentOut, status_code=201)
def create_document(payload: DocumentCreate, db: Session = Depends(get_db)):
    doc = Document(**payload.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@app.put("/api/documents/{doc_id}", response_model=DocumentOut)
def update_document(doc_id: int, payload: DocumentUpdate, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(doc, key, value)
    db.commit()
    db.refresh(doc)
    return doc


@app.delete("/api/documents/{doc_id}", status_code=204)
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    db.delete(doc)
    db.commit()
    return None


# ---------- 上传整个文件夹 ----------
@app.post("/api/upload-folder")
def upload_folder(payload: UploadFolderRequest, db: Session = Depends(get_db)):
    """根据前端传来的 [相对路径, 内容] 列表，重建目录结构并落库。

    例如 path = "算法/排序/快排.md" → 建文件夹 算法 → 排序 → 文档 快排.md。
    """
    folders_created = 0
    docs_created = 0
    for item in payload.files:
        parts = [p for p in item.path.replace("\\", "/").split("/") if p]
        if not parts:
            continue
        # 逐级查找或创建文件夹
        parent_id = None
        for name in parts[:-1]:
            folder = (
                db.query(Folder)
                .filter(Folder.name == name, Folder.parent_id == parent_id, Folder.kind == payload.kind)
                .first()
            )
            if not folder:
                folder = Folder(name=name, parent_id=parent_id, kind=payload.kind)
                db.add(folder)
                db.flush()
                folders_created += 1
            parent_id = folder.id
        if parent_id is None:
            # 理论上不会发生（上传文件夹时路径至少含文件夹名）
            continue
        db.add(Document(folder_id=parent_id, title=parts[-1], content=item.content, tags=[]))
        docs_created += 1
    db.commit()
    return {"folders_created": folders_created, "documents_created": docs_created}
