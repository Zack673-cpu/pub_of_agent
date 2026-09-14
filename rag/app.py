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
from rag.auth import hash_refresh_token,create_refresh_token_plain,create_access_token,hash_password,verify_password
from backend.models import RefreshToken, User
from datetime import datetime,timezone,timedelta
from sqlalchemy.exc import IntegrityError




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

TOKEN ="123456"




files=StaticFiles(directory="frontend",html=True)

app.mount("/frontend",files,name="frontend")

class QUESTION (BaseModel):
    Question:str

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

@app.post("/ask")
async def answer_agent(question:QUESTION,authorization: str=Header(default=None)):
                                            #调用了Header函数获取请求头里的authorization字段的值
    
    if authorization!=TOKEN:
        raise HTTPException(status_code=401, detail="   鉴权错误，token值不对！")

    

    try:
        answer=rag.ask(question.Question,db.fetch_history(5))
    except Exception as e:
        logger.error("/ask出错",exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    id=db.save_record(question.Question,answer)

   


    return {"智能体回答：":answer}


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

    