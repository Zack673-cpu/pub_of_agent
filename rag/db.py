#模块启动，数据库动作

from pathlib import Path
import os
import pymysql
from dotenv import load_dotenv
import logging
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime,timezone
import sys
from enum import Enum
from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),           # 终端
        logging.FileHandler(Path(__file__).parent/"app.log", encoding="utf-8"),  # 文件
    ]
)
logger = logging.getLogger(__name__)
load_dotenv()


password=os.getenv("DB_PASSWORD")
if password is None:
    logger.error("    DB_PASSWORD 为空，检查 .env 文件")
    sys.exit()


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


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True,nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20), default="editor")
    # relationship: 一对多，一个用户有多本书
    books: Mapped[list["Book"]] = relationship(back_populates="user")


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

class OutlineVersion (Base):
    __tablename__= "outline_versions"
    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    book_id: Mapped[int]=mapped_column(ForeignKey("books.id"))
    version_no :Mapped[int]=mapped_column()
    tree_json:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),nullable=False)
    


class OutlineStaging(Base):
    __tablename__="outline_staging"
    book_id :Mapped[int]=mapped_column(ForeignKey("books.id"),primary_key=True)
    tree_json:Mapped[str]=mapped_column(Text)
    updated_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),nullable=False)


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


class DraftVersion(Base):
    __tablename__="draft_versions"
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    book_id:Mapped[int]=mapped_column(ForeignKey("books.id"),nullable=False)
    section_id:Mapped[int]=mapped_column(ForeignKey("sections.id"),nullable=False)
    version_no:Mapped[int]=mapped_column()
    content:Mapped[str]=mapped_column(Text)
    diff_ops_json:Mapped[str]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),nullable=False)



class Staging(Base):
    __tablename__="staging"
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    section_id:Mapped[int]=mapped_column(ForeignKey("sections.id"),nullable=False)
    content:Mapped[str]=mapped_column(Text)
    updated_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),nullable=False)



class EditPair (Base):
    __tablename__="edit_pairs"
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)

    book_id:Mapped [int]=mapped_column(ForeignKey("books.id")) 
    section_id:Mapped[int|None]=mapped_column(ForeignKey("sections.id")) 
    granularity:Mapped[EditGranularityEnum]=mapped_column(SAEnum(EditGranularityEnum,name="edit_pairs_granularity"))
    old_text:Mapped[str]=mapped_column(Text)
    new_text:Mapped[str]=mapped_column(Text)
    context_before:Mapped[str]=mapped_column(Text,nullable=True)
    context_after:Mapped[str]=mapped_column(Text,nullable=True)	
    diff_ops_json:Mapped[str]=mapped_column(Text)
    source:Mapped[EditSourceEnum]=mapped_column(SAEnum(EditSourceEnum,name="edit_pairs_source"))
    created_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),nullable=False)



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


class Task(Base):
    __tablename__="tasks"
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    book_id:Mapped [int]=mapped_column(ForeignKey("books.id")) 
    kind:Mapped[TasksKindEnum]=mapped_column(SAEnum(TasksKindEnum,name="tasks_kind"))
    status:Mapped[str]=mapped_column(Text)
    progress_json:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),nullable=False)









db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': password,  # 若无密码则留空 ''
    'port': 3306,
    'charset': 'utf8mb4'
}

db_name="textbook_agent"

def init_db(): # 建三张表，幂等（重复跑不报错）
    connection=pymysql.connect(**db_config)   
    try :
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARSET utf8mb4")
            cursor.execute(f"USE {db_name}")

            create_table_sql="""
            CREATE TABLE IF NOT EXISTS conversations (
                id int primary key auto_increment,
                question text not null,
                answer text not null,
                created_at timestamp default current_timestamp
            );"""
            cursor.execute(create_table_sql)

            create_table_sql="""
            CREATE TABLE IF NOT EXISTS outlines (
                id int primary key auto_increment,
                title varchar(100) not null,
                content text ,
                created_at timestamp default current_timestamp
            );"""
            cursor.execute(create_table_sql)


            create_table_sql="""
            CREATE TABLE IF NOT EXISTS drafts (
                id int primary key auto_increment,
                title varchar(100) not null,
                content text ,
                status varchar(20),
                created_at timestamp default current_timestamp
            );"""
            cursor.execute(create_table_sql)
    except pymysql.Error as e:
        print(f"  初始化失败: {e}")

    finally:
        connection.close()
                                
def save_record(question: str, answer: str) -> int:
    save_connection=pymysql.connect(**db_config)   
    id=-1
    sql=r"""
        INSERT INTO conversations (question,answer) VALUES (%s,%s)
    """
    try:
        with save_connection.cursor() as cursor:
            cursor.execute(f"USE {db_name}")
            cursor.execute(sql,(question,answer))
            save_connection.commit()
            id=cursor.lastrowid
    except pymysql.Error as e:
        print(f"  保存数据失败：{e}")
    finally:
        
        save_connection.close()

    return id


 # 取最近 limit 条，数据形状：[("问题1","回答1"), ("问题2","回答2"), ...]


def fetch_history(limit: int) -> list[tuple]:
    fetch_connection = pymysql.connect(**db_config)
    fetch_result=[]
    try:
        with fetch_connection.cursor() as cursor:
            cursor.execute(f"USE {db_name}")
            
            cursor.execute("select question,answer from conversations order by created_at desc limit %s",(limit,))
            fetch_result=list(cursor.fetchall())
            fetch_result.reverse()
            return fetch_result
    except pymysql.Error as e:
        print(f"   获取最近的{limit}条数据失败：{e}")
        return []
    finally:
        fetch_connection.close()

   



def drop_database():
    database=db_name
    Confirm=input(f"确认删除数据库{database}？Y/N：")
    if Confirm.lower()=='y':
        delete_connection=pymysql.connect(**db_config)
        try :
            with delete_connection.cursor() as cursor:
                cursor.execute(f"DROP DATABASE  IF EXISTS {database};")
                print(f" 删除{database}成功！")
        except pymysql.Error as e:
            print(f"   删库失败：{e}")
        finally:
            delete_connection.close()
    else : return


def main():
    drop_database()
    init_db()
    
    # id=save_record("示例问题","示例答案")
    # print(id,"\n")

    # history=fetch_history(10)
    # print(type(history),"\n",history)

if __name__ == '__main__':
    main()


