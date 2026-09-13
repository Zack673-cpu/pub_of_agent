from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, UniqueConstraint, ForeignKey, Enum as SAEnum
from datetime import datetime, timezone
from enum import Enum

class Base(DeclarativeBase):
    pass


class BookStatusEnum (Enum):
    drafting="drafting"
    submitted="submitted"


class SectionStatusEnum(Enum):
    empty="empty"
    generated="generated"
    failed="failed"
# 节状态

class EditGranularityEnum(Enum):
    outline="outline"
    passage="passage"
    section="section"
# outline=问题→大纲, passage=问题→小节, section=AI初稿→人工定稿


class EditSourceEnum(Enum):
    user="user"
    ai="ai"

class TasksKindEnum(Enum):
    outline="outline"
    book="book"
    section="section"
    rewrite="rewrite"
    outline_revise="outline_revise"
    intent="intent"

class TasksStatusEnum(Enum):
    pending="pending"
    running="running"
    done="done"
    failed="failed"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True,nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20), default="editor")
    # relationship: 一对多，一个用户有多本书
    books: Mapped[list["Book"]] = relationship(back_populates="user",cascade="all,delete-orphan")
    refresh_tokens:Mapped[list["RefreshToken"]]=relationship(back_populates="user",cascade="all,delete-orphan")

class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    requirement:Mapped[str]= mapped_column(Text)
    status:Mapped[BookStatusEnum]=mapped_column(SAEnum(BookStatusEnum,name="books_status"),nullable=False)
    created_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),nullable=False)
    updated_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc),nullable=False)
    user: Mapped["User"] = relationship(back_populates="books")
    outline_versions:Mapped[list["OutlineVersion"]]=relationship(back_populates="book",cascade="all,delete-orphan")
    outline_staging:Mapped["OutlineStaging"]=relationship(back_populates="book",cascade="all,delete-orphan")
    sections:Mapped[list["Section"]]=relationship(back_populates="book",cascade="all,delete-orphan")
    tasks:Mapped[list["Task"]]=relationship(back_populates="book",cascade="all,delete-orphan")
    edit_pairs:Mapped[list["EditPair"]]=relationship(back_populates="book",cascade="all,delete-orphan")
    draft_versions:Mapped[list["DraftVersion"]]=relationship(back_populates="book",cascade="all,delete-orphan")
    rewrite_requests:Mapped[list["RewriteRequest"]]=relationship(back_populates="book",cascade="all,delete-orphan")


class OutlineVersion (Base):
    __tablename__= "outline_versions"
    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    book_id: Mapped[int]=mapped_column(ForeignKey("books.id"))
    version_no :Mapped[int]=mapped_column()
    tree_json:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),nullable=False)
    book:Mapped["Book"]=relationship(back_populates="outline_versions")
    tasks:Mapped[list["Task"]]=relationship(back_populates="outline_version",cascade="all,delete-orphan")

class OutlineStaging(Base):
    __tablename__="outline_staging"
    book_id :Mapped[int]=mapped_column(ForeignKey("books.id"),primary_key=True)
    tree_json:Mapped[str]=mapped_column(Text)
    updated_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc),nullable=False)
    book:Mapped["Book"]=relationship(back_populates="outline_staging")

class Section(Base):
    __tablename__="sections"    

    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    book_id:Mapped[int]=mapped_column(ForeignKey("books.id"),nullable=False)
    node_key :Mapped[str]=mapped_column(String(200),nullable=False)
    title:Mapped[str]=mapped_column(String(200))
    order_no:Mapped[int]=mapped_column()
    parent_key:Mapped[str]=mapped_column(String(200),nullable=True)
    status:Mapped[SectionStatusEnum]=mapped_column(SAEnum(SectionStatusEnum,name="sections_status"),nullable=False)
    discarded:Mapped[bool]=mapped_column(default=False)
    book:Mapped[Book]=relationship(back_populates="sections")
    draft_versions:Mapped[list["DraftVersion"]]=relationship(back_populates="section",cascade="all,delete-orphan")
    staging:Mapped["Staging"]=relationship(back_populates="section",cascade="all,delete-orphan")
    edit_pairs :Mapped[list["EditPair"]]=relationship(back_populates="section",cascade="all,delete-orphan")
    rewrite_requests:Mapped[list["RewriteRequest"]]=relationship(back_populates="section",cascade="all,delete-orphan")
    tasks:Mapped[list["Task"]]=relationship(back_populates="section",cascade="all,delete-orphan")
    __table_args__=(UniqueConstraint('book_id', 'node_key', name='uq_sections_book_node'),)


class DraftVersion(Base):
    __tablename__="draft_versions"
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    book_id:Mapped[int]=mapped_column(ForeignKey("books.id"),nullable=False)
    section_id:Mapped[int]=mapped_column(ForeignKey("sections.id"),nullable=False)
    version_no:Mapped[int]=mapped_column()
    content:Mapped[str]=mapped_column(Text)
    diff_ops_json:Mapped[str]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),nullable=False)
    book:Mapped[Book]=relationship(back_populates="draft_versions")
    section:Mapped[Section]=relationship(back_populates="draft_versions")

class Staging(Base):
    __tablename__="staging"
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    section_id:Mapped[int]=mapped_column(ForeignKey("sections.id"),nullable=False)
    content:Mapped[str]=mapped_column(Text)
    updated_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc),nullable=False)
    section:Mapped[Section]=relationship(back_populates="staging")


class EditPair (Base):
    __tablename__="edit_pairs"
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)

    book_id:Mapped [int]=mapped_column(ForeignKey("books.id")) 
    section_id:Mapped[int|None]=mapped_column(ForeignKey("sections.id")) 
    granularity:Mapped[EditGranularityEnum]=mapped_column(SAEnum(EditGranularityEnum,name="edit_pairs_granularity"))
    old_text:Mapped[str]=mapped_column(Text)
    new_text:Mapped[str]=mapped_column(Text)
    context_before:Mapped[str|None]=mapped_column(Text,nullable=True)
    context_after:Mapped[str|None]=mapped_column(Text,nullable=True)	
    diff_ops_json:Mapped[str|None]=mapped_column(Text)
    source:Mapped[EditSourceEnum]=mapped_column(SAEnum(EditSourceEnum,name="edit_pairs_source"))
    created_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),nullable=False)
    book:Mapped[Book]=relationship(back_populates="edit_pairs")
    section:Mapped[Section|None]=relationship(back_populates="edit_pairs")

class RewriteRequest (Base):
    __tablename__="rewrite_requests"
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    book_id:Mapped [int]=mapped_column(ForeignKey("books.id")) 
    section_id:Mapped[int]=mapped_column(ForeignKey("sections.id")) 
    start_offset:Mapped[int]=mapped_column()
    end_offset:Mapped[int]=mapped_column()
    instruction:Mapped[str]=mapped_column(Text)
    old_passage:Mapped[str]=mapped_column(Text)
    new_passage:Mapped[str]=mapped_column(Text)
    book:Mapped[Book]=relationship(back_populates="rewrite_requests")
    section:Mapped[Section]=relationship(back_populates="rewrite_requests")

class Task(Base):
    __tablename__="tasks"
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    book_id:Mapped [int]=mapped_column(ForeignKey("books.id")) 
    section_id:Mapped[int|None]=mapped_column(ForeignKey("sections.id"),nullable=True)
    outline_version_id:Mapped[int|None]=mapped_column(ForeignKey("outline_versions.id"),nullable=True)
    kind:Mapped[TasksKindEnum]=mapped_column(SAEnum(TasksKindEnum,name="tasks_kind"))
    status:Mapped[TasksStatusEnum]=mapped_column(SAEnum(TasksStatusEnum,name="tasks_status"))
    progress_json:Mapped[str|None]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),nullable=False)
    book:Mapped[Book]=relationship(back_populates="tasks")
    section:Mapped[Section|None]=relationship(back_populates="tasks")
    outline_version:Mapped[OutlineVersion|None]=relationship(back_populates="tasks")


class RefreshToken(Base):
    __tablename__="refresh_tokens"
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"))    
    token:Mapped[str]=mapped_column(String(64))     
    expires_at:Mapped[datetime]=mapped_column(nullable=False)
    revoked:Mapped[bool]=mapped_column(default=False)     
    created_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),nullable=False)
    user:Mapped["User"]=relationship(back_populates="refresh_tokens")
    #   关系：多个 token 属于一个用户（多对一）
    __table_args__=(UniqueConstraint('token',name='uq_token'),)



