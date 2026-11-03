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


# ---------- 能力证据 ----------
class ExtractAbilitiesRequest(BaseModel):
    document_ids: List[int]  # 用户勾选的文档 id 列表


class ExtractFolderRequest(BaseModel):
    folder_id: int  # 抽取该文件夹（含子文件夹）下所有文档


class AbilityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    kind: Optional[str] = None
    source: Optional[str] = None
    confirmed: Optional[bool] = None


class AbilityBatchDelete(BaseModel):
    ids: List[int]  # 批量删除的能力 id 列表


class GenerateResumeSkillsRequest(BaseModel):
    ability_ids: List[int]  # 用户勾选的能力 id 列表
    target_position: str  # 目标岗位，如「C++ 后端开发工程师」


class AbilityOut(BaseModel):
    id: int
    kind: str
    name: str
    description: str
    source: Optional[str]
    confirmed: bool
    created_at: datetime

    class Config:
        from_attributes = True
