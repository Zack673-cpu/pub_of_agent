import rag.db as db
import rag.rag as rag
from fastapi import FastAPI,Depends,Header,HTTPException
from pydantic import BaseModel,Field
from fastapi.staticfiles import StaticFiles
import rag.pipeline as pipeline
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from backend.database import get_session
from sqlalchemy.orm import Session
from rag.auth import hash_refresh_token,create_refresh_token_plain,create_access_token,hash_password,verify_password,verify_access_token
from backend.models import RefreshToken, User,Book,OutlineStaging,OutlineVersion,Section,Staging,DraftVersion
from datetime import datetime,timezone,timedelta
from sqlalchemy.exc import IntegrityError
from fastapi.middleware.cors import CORSMiddleware
import json


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
if(os.getenv("DASHSCOPE_API_KEY") is None):
    logger.warning("DASHSCOPE_API_KEY 为空，检查.env文件")

if not rag.restore_path.exists():
    logger.warning(f"向量库文件不存在：{rag.restore_path}")
if not rag.doc_path.exists():
    logger.warning(f"语料库文件不存在：{rag.doc_path}")

#模块启动
app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,  # 因为你会带 cookie/session 才开，JWT 走 header 时可考虑
    allow_methods=["*"],     # 允许的 HTTP 方法
    allow_headers=["*"],     # 允许的请求头（你的自定义 Authorization 头要靠它放行）
)



TOKEN ="123456"




files=StaticFiles(directory="frontend",html=True)

app.mount("/frontend",files,name="frontend")



class OUTLINE (BaseModel):
    Topic:str

class SECTION(BaseModel):
    Section:str

class RefreshBody(BaseModel):
    refresh_token: str
class RegisterBody(BaseModel):
    username:str=Field(...,min_length=3,max_length=20)
    password:str=Field(...,min_length=5)
class LoginBody(BaseModel):
    username:str
    password:str
class CreateBookBody(BaseModel):
    title:str 
    requirement:str



@app.post("/outline")
async def outline_agent(outline:OUTLINE,authorization:str =Header (default=None)):
    if authorization!=TOKEN:
        raise HTTPException(status_code=401, detail= "   鉴权错误，token值不对！")
    try :
        out=pipeline.generate_outline(outline.Topic)
    except Exception as e:
        logger.error("/outline出错",exc_info=True)
        raise HTTPException(status_code=500,detail=str(e))

    return {"大纲：":out}


#这里实际接上的应该是整个大纲，按照大纲写作出整篇教材而不是一节，后续扩展，现在就按照接收一节来
@app.post("/generate")
async def generate_agent(section:SECTION,authorization: str=Header(default=None)):
    if authorization!=TOKEN:
        raise HTTPException(status_code=401, detail="   鉴权错误，token值不对！")

    try:
        draft=pipeline.generate_section(section.Section)
    except Exception as e:
        logger.error("/generate出错",exc_info=True)
        raise HTTPException(status_code=500,detail=str(e))

    return {"初稿：":draft}


@app.post("/refresh")
async def refresh_token(body: RefreshBody, db: Session = Depends(get_session)):
    #这个函数直接换两种token
    #db：参数名。
    #Session：类型注解，表示你期望 db 是 Session 类型。
    #Depends(get_session)：告诉 FastAPI，这个参数不要从请求里解析，而是调用 get_session 来获取。
    #FastAPI 会调用 get_session，把结果注入给 db。
    now=datetime.now(timezone.utc)
    plain=body.refresh_token
    token_hash = hash_refresh_token(plain) 
    row = db.query(RefreshToken).filter(RefreshToken.token == token_hash).first()
        #针对某个表查询            筛选条件                            取第一行结果


    if row is None:
        raise HTTPException(status_code=401,detail="    refresh token 查询不到")

    expires_at=row.expires_at
    expires_at=expires_at.replace(tzinfo=timezone.utc)
    
    if row.revoked is True:
        raise HTTPException(status_code=401,detail="    refresh token 已吊销")
    elif expires_at< now:
        raise HTTPException(status_code=401,detail="    refresh token 已过期")
    else:
        try:
            row.revoked=True
            refresh_plain=create_refresh_token_plain()
            #新明文
            refresh_token_hashed=hash_refresh_token(refresh_plain)
            #新哈希
            new_row=RefreshToken(
                user_id=row.user_id,
                token=refresh_token_hashed,
                expires_at=now+timedelta(days=7),
                revoked=False,
            )
            new_access=create_access_token(row.user_id)
            db.add(new_row)
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500,detail=str(e))
        
        return {"access_token":new_access,"refresh_token":refresh_plain}


@app.post("/register")
async def register(body:RegisterBody,db:Session=Depends(get_session)):
    #查重，插入新用户，发双token，其中refresh进库
    check=db.query(User).filter(User.username==body.username).first()
    if check is not None:
        raise HTTPException(status_code=400,detail="   用户名已经被使用")
    else:            
        password_hashed=hash_password(body.password)
        new_row=User(
            username=body.username,
            password_hash=password_hashed,
        )
        try:
            db.add(new_row)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="   用户名已经被使用")

        now=datetime.now(timezone.utc)
        userid=new_row.id
        access_token=create_access_token(userid)
        refresh_token=create_refresh_token_plain()
        refresh_token_hashed=hash_refresh_token(refresh_token)

        try:
            new_row=RefreshToken(
                user_id=userid,
                token=refresh_token_hashed,
                expires_at=now+timedelta(days=7),
                revoked=False,
            )
            db.add(new_row)
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500,detail=str(e))
        
        return {"message":"注册成功","access_token":access_token,"refresh_token":refresh_token}



@app.post("/login")
async def login(body:LoginBody,db:Session=Depends(get_session)):
    user=db.query(User).filter(User.username==body.username).first()
    if user is None:
        raise HTTPException(status_code=401,detail="    用户名或密码错误")
    else:
        check=verify_password(body.password,user.password_hash)
        if check is False:
            raise HTTPException(status_code=401,detail="    用户名或密码错误")
        now=datetime.now(timezone.utc)
        userid=user.id
        access_token=create_access_token(userid)
        refresh_token=create_refresh_token_plain()
        refresh_token_hashed=hash_refresh_token(refresh_token)

        try:
            new_row=RefreshToken(
                user_id=userid,
                token=refresh_token_hashed,
                expires_at=now+timedelta(days=7),
                revoked=False,
            )
            db.add(new_row)
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500,detail=str(e))
        
        return {"message":"登录成功","access_token":access_token,"refresh_token":refresh_token}

@app.post("/books")
async def create_book(body:CreateBookBody,authorization:str=Header(default=None),db:Session=Depends(get_session)):
    if authorization is None:
        raise HTTPException(status_code=401,detail="   access_token没有拿到")
    if authorization.startswith("Bearer ") is False:
        raise HTTPException(status_code=401,detail="    access_token格式不对")
    
    authorization=authorization.removeprefix("Bearer ")
    try:
        user_id=verify_access_token(authorization)
    except Exception as e:
        raise HTTPException(status_code=401,detail="    access_token解析失败，原因："+str(e))
    try:
        new=Book(
            user_id=user_id,
            title=body.title,
            requirement=body.requirement,
        )
        db.add(new)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
    return {"id":new.id,"title":new.title,"requirement":new.requirement,"status":new.status,"created_at":new.created_at}

@app.get("/books")
async def list_books(authorization: str =Header(default=None),db:Session=Depends(get_session)):
    if authorization is None:
        raise HTTPException(status_code=401,detail="   access_token没有拿到")
    if authorization.startswith("Bearer ") is False:
        raise HTTPException(status_code=401,detail="    access_token格式不对")
    
    authorization=authorization.removeprefix("Bearer ")
    try:
        user_id=verify_access_token(authorization)
    except Exception as e:
        raise HTTPException(status_code=401,detail="    access_token解析失败，原因："+str(e))
 
    res=[]
    try:
        row=db.query(Book).filter(user_id==Book.user_id).order_by(Book.created_at.desc()).all()
        for book in row:
            
            created_at=book.created_at
            created_at=created_at.replace(tzinfo=timezone.utc).isoformat()
            updated_at=book.updated_at
            updated_at=updated_at.replace(tzinfo=timezone.utc).isoformat()
            res.append({"id":book.id,"title":book.title,"requirement":book.requirement,"status":book.status,"created_at":created_at,"updated_at":updated_at})

    except Exception as e:
        raise e
    return {"books":res}



@app.get("/books/{book_id}")
async def get_book(book_id:int ,authorization:str=Header(default=None),db:Session=Depends(get_session)):
    if authorization is None:
        raise HTTPException(status_code=401,detail="   access_token没有拿到")
    if authorization.startswith("Bearer ") is False:
        raise HTTPException(status_code=401,detail="    access_token格式不对")
    
    authorization=authorization.removeprefix("Bearer ")
    try:
        user_id=verify_access_token(authorization)
    except Exception as e:
        raise HTTPException(status_code=401,detail="    access_token解析失败，原因："+str(e))

    try:
        row=db.query(Book).filter(book_id==Book.id).first()
    except Exception as e:
        raise e
    if row is None:
        raise HTTPException(status_code=404,detail="    查不到书籍")
    if row.user_id!=user_id:
        raise HTTPException(status_code=403,detail="    归属错误")
    
    created_at=row.created_at
    created_at=created_at.replace(tzinfo=timezone.utc).isoformat()
    updated_at=row.updated_at
    updated_at=updated_at.replace(tzinfo=timezone.utc).isoformat()

    return {"id":row.id,"title":row.title,"requirement":row.requirement,"status":row.status,"created_at":created_at,"updated_at":updated_at}


@app.put("/books/{book_id}/outline/staging")
async def save_outline_staging(book_id: int, body: dict, authorization: str = Header(default=None), db: Session = Depends(get_session)):
    if authorization is None:
        raise HTTPException(status_code=401,detail="   access_token没有拿到")
    if authorization.startswith("Bearer ") is False:
        raise HTTPException(status_code=401,detail="    access_token格式不对")
    
    authorization=authorization.removeprefix("Bearer ")
    try:
        user_id=verify_access_token(authorization)
    except Exception as e:
        raise HTTPException(status_code=401,detail="    access_token解析失败，原因："+str(e))

    
    try:

        row=db.get(OutlineStaging,book_id)
        book=db.get(Book,book_id)
        tree=json.dumps(body, ensure_ascii=False)
    except Exception as e:
        raise e    
    if book is None:
        raise HTTPException(status_code=404,detail="    书籍查不到")
    if book.user_id!=user_id:
        raise HTTPException(status_code=403,detail="    归属错误")
    if row is None:
        try:
            row=OutlineStaging(
                book_id=book_id,
                tree_json=tree,
            )
            db.add(row)
            db.commit()

        except Exception as e:
            raise e
    else:
        try:
            row.tree_json=tree
            db.commit()
        except Exception as e:
            raise e

    return {"book_id":book_id, "updated_at": row.updated_at.replace(tzinfo=timezone.utc).isoformat()}



@app.get("/books/{book_id}/outline/versions")
async def list_outline_versions(book_id: int, authorization: str = Header(default=None), db: Session = Depends(get_session)):
    if authorization is None:
        raise HTTPException(status_code=401,detail="   access_token没有拿到")
    if authorization.startswith("Bearer ") is False:
        raise HTTPException(status_code=401,detail="    access_token格式不对")
    authorization=authorization.removeprefix("Bearer ")
    try:
        user_id=verify_access_token(authorization)
    except Exception as e:
        raise HTTPException(status_code=401,detail="    access_token解析失败，原因："+str(e))

    try:
        row=db.query(OutlineVersion).filter(OutlineVersion.book_id==book_id).order_by(OutlineVersion.version_no.asc()).all()
        book=db.get(Book,book_id)
    except Exception as e:
        raise e
    if book is None:
        raise HTTPException(status_code=404,detail="    书籍查不到")
    if book.user_id!=user_id:
        raise HTTPException(status_code=403,detail="    归属错误")
    res=[]
    for v in row:
        tree=json.loads(v.tree_json)
        res.append({"id":v.id,"version_no":v.version_no,"tree_json":tree,"created_at":v.created_at.replace(tzinfo=timezone.utc).isoformat()})


    return {"versions":res}


@app.put("/sections/{id}/staging")
async def save_section_staging(id:int,body: dict, authorization: str = Header(default=None), db: Session = Depends(get_session)):
    if authorization is None:
        raise HTTPException(status_code=401,detail="   access_token没有拿到")
    if authorization.startswith("Bearer ") is False:
        raise HTTPException(status_code=401,detail="    access_token格式不对")
    authorization=authorization.removeprefix("Bearer ")
    try:
        user_id=verify_access_token(authorization)
    except Exception as e:
        raise HTTPException(status_code=401,detail="    access_token解析失败，原因："+str(e))

    try:
        row=db.get(Section,id)
        # row.staging 就是暂存行，因为建立了relationship
        # row.book 就是对应的书，因为建立了relationship
    except Exception as e:
        raise e
    if row is None:
        raise HTTPException(status_code=404,detail="    章节不存在")
        #后面会批量生成章节id，所以是为了防止传错id    
    if row.book is None:
        raise HTTPException(status_code=404,detail="    书籍查不到")
    if row.book.user_id!=user_id:
        raise HTTPException(status_code=403,detail="    归属错误")
    if 'content' in body:
        if body["content"] is None:
            raise HTTPException(status_code=422, detail="   正文错误，字典的content值为None")
        content=body["content"]
    elif 'content' not in body:
        raise HTTPException(status_code=422,detail="    正文错误，字典的content值没有传")        
    

    
    if row.staging is None:
        #这里才是说明新建的还没有暂存
        try:
            row.staging=Staging(
                section_id=id,
                content=content,
            )
            db.commit()
        except Exception as e:
            raise e
    else:
        try:
            row.staging.content=content
            db.commit()
        except Exception as e:
            raise e
        
    return {"section_id": id, "updated_at": row.staging.updated_at.replace(tzinfo=timezone.utc).isoformat()}

@app.get("/sections/{id}/versions")
async def list_section_versions(id:int,authorization: str = Header(default=None), db: Session = Depends(get_session)):
    if authorization is None:
        raise HTTPException(status_code=401,detail="   access_token没有拿到")
    if authorization.startswith("Bearer ") is False:
        raise HTTPException(status_code=401,detail="    access_token格式不对")
    authorization=authorization.removeprefix("Bearer ")
    try:
        user_id=verify_access_token(authorization)
    except Exception as e:
        raise HTTPException(status_code=401,detail="    access_token解析失败，原因："+str(e))

    try:
        row=db.get(Section, id)
        draft_versions=db.query(DraftVersion).filter(DraftVersion.section_id==id).order_by(DraftVersion.version_no.asc()).all()
    except Exception as e:
        raise e
    if row is None:
        raise HTTPException(status_code=404,detail="    章节不存在")
    if row.book is None:
        raise HTTPException(status_code=404,detail="    书籍查不到")
    if row.book.user_id!=user_id:
        raise HTTPException(status_code=403,detail="    归属错误")
    
    res=[]
    for v in draft_versions:
        created_at=v.created_at.replace(tzinfo=timezone.utc).isoformat()
        res.append({'id':v.id,'version_no':v.version_no,'content':v.content,'created_at':created_at})

    return {'versions':res}