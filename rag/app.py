

from requests import status_codes

import rag.db as db
import rag.rag as rag
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi import Header,HTTPException
#模块启动
app=FastAPI()

TOKEN ="123456"

class QUESTION (BaseModel):
    Question:str

files=StaticFiles(directory="frontend",html=True)

app.mount("/frontend",files,name="frontend")





@app.post("/ask")
async def answer_agent(question:QUESTION,authorization: str=Header(default=None)):
                                            #调用了Header函数获取请求头里的authorization字段的值
    
    if authorization!=TOKEN:
        raise HTTPException(status_code=401, detail="   鉴权错误，token值不对！")

    

    try:
        answer=rag.ask(question.Question,db.fetch_history(5))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    id=db.save_record(question.Question,answer)

   


    return {"智能体回答：":answer}



