"""Pydantic 请求 / 响应模型。"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None
    kind: str = "note"


class FolderUpdate(BaseModel):
    name: str


class FolderOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    kind: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    folder_id: int
    title: str = ""
    content: str = ""
    tags: List[str] = []


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class DocumentOut(BaseModel):
    id: int
    folder_id: int
    title: str
    content: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UploadFileItem(BaseModel):
    path: str      # 相对路径，如 "算法/排序/快排.md"
    content: str   # 文件文本内容


class UploadFolderRequest(BaseModel):
    kind: str = "note"
    files: List[UploadFileItem]
