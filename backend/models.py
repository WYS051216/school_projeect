"""数据表模型定义。

数据结构：文件夹树 + 文档。
    Folder   ：文件夹节点，parent_id 指向父文件夹，支持多层嵌套。   
    Document ：文件夹下的一篇 Markdown / 文本文档。
kind 字段区分两个大区：note(笔记) / project(项目经历)。
"""
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from database import Base


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("folders.id"), nullable=True)  # null = 顶层文件夹
    kind = Column(String(20), nullable=False, default="note")  # note / project
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=False)
    title = Column(String(200), nullable=False, default="")
    content = Column(Text, nullable=False, default="")
    tags = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Ability(Base):
    """能力证据：大模型从笔记 / 项目经历中抽取出的结构化能力条目。"""

    __tablename__ = "abilities"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(20), nullable=False, default="skill")  # skill / project / achievement
    name = Column(String(200), nullable=False)  # 技能名 / 项目名 / 成果名
    description = Column(Text, nullable=False, default="")  # 详细描述
    source = Column(String(200), nullable=True)  # 来源文档标题（可追溯）
    confirmed = Column(Boolean, nullable=False, default=False)  # 用户是否确认
    created_at = Column(DateTime, default=datetime.utcnow)
