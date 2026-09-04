from requests import status_codes
import rag.db as db
import rag.rag as rag
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi import Header,HTTPException
import rag.pipeline as pipeline
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
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