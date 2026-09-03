
from email import message
from pathlib import Path
import math
import os
from dotenv import load_dotenv
import requests
import json
import rag.llm as llm
import time
#模块启动
load_dotenv() 

doc_path=Path(r"rag\corpus\example-note.md") #原始语料地址

restore_path=Path(r"rag\vector_store.json")  #语料和向量存储地址




#清洗函数  接收str，返回str
def clean_up(text):
    delete="\n#"
    trans_table=str.maketrans('','',delete)
    s=text.translate(trans_table)
    return s


#切成文字块  接收str,返回list[str]
def to_chunks(text,size=200,overlap=50):
    chunks=[]
    for i in range(0,len(text),(size-overlap)):
        chunks.append(text[i:i+size])

    return chunks

def cos(a: list[float], b: list[float]) -> float:
    # 你已有 cos 的数学不用变，但输入形状从 dict 变成 list[float]
    fenmu=1;
    z_a=0;z_b=0;
    for i in a:
        z_a+=i*i;
    z_a=math.sqrt(z_a)
    for j in b:
        z_b+=j*j;
    z_b=math.sqrt(z_b)
    fenmu=z_a*z_b;
    if fenmu ==0:
        return 0;

    fenzi=0;
    for i in range(0,len(a)):
        if i <len(b): fenzi+=a[i]*b[i]

    return fenzi/fenmu 










def get_embedding(text: str) -> list[float]:
    # 调 DashScope text-embedding API，返回向量
    
    key = os.getenv("DASHSCOPE_API_KEY")
    if key is None: raise ValueError(r"api key获取出错，检查pub_of_agent\.env")

    # 用 requests.post（环境里有），请求格式查官方文档
    url="https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
    headers = {
        "Authorization": "Bearer " + key,   # 鉴权
        "Content-Type": "application/json"
    }
    body = {
        "model": "text-embedding-v4",       # ← 就是这一行决定调哪个模型
        "input": {"texts": [text]}           # 待向量化的文本，注意 texts 是列表
    }

    max_retries = 3
    for attempt in range(0,max_retries):
        try:    
            result=requests.post(url, headers=headers, json=body,timeout=30)
            result.raise_for_status()
            data=result.json()
            # key 从环境变量读：os.getenv("DASHSCOPE_API_KEY")——key 绝不写死在代码里
            # print(type(result.json()),result.json())
            # dict{"output":dict{"embeddings":list[(这个list对应传的第几块语料){"embedding":list[float(这个才是向量)], ] , }  ,}
            vector=data["output"]["embeddings"][0]["embedding"]
            # print(len(vector))
            return vector
        except (requests.Timeout, requests.ConnectionError) as e:
            # 网络错误：重试
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"   Embedding API 网络错误（重试{max_retries}次）：{e}")
        except requests.HTTPError as e:
            # HTTP 错误：5xx 重试，4xx 不重试
            if e.response.status_code >= 500 and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"   Embedding API 返回错误：{e}")
        except (KeyError, ValueError) as e:
            # 解析失败：不重试
            raise RuntimeError(f"   Embedding API 响应解析失败：{e}")



# 离线索引：读语料 → 切块 → 逐块变向量 → 存文件（块文本和向量一起存，召回时要返回文本）
def build_index():
    with open (doc_path,'r',encoding='utf-8') as f:
        yuliao=f.read()
    text=clean_up(yuliao)
    chunks=to_chunks(text)

    res=[]
    for i in range(0,len(chunks)):
        res.append({
            "text":chunks[i],
            "vector":get_embedding(chunks[i])
        })

    # for item in res:
    #     print(f"{{'text': {item['text']!r}, 'vector': [...]}}")

    with open(restore_path,"w",encoding="utf-8") as f:
        json.dump(res,f,ensure_ascii=False)


    return;



# ask() 改造：删掉 tfidf 那几行，换成 load 向量库 → 问题向量化 → retrieve


#召回，计算相似度并返回得分最高的2块
def retrieve(question_vector,chunks_vectors,top_k=2):
    #chunks_vectors=list[{"text","vector":list[float]}]
    #question_vector=list[float]

    scores=[]   #[(float,str)]
    for i in range(0,len(chunks_vectors)):
        scores.append((cos(chunks_vectors[i]["vector"],question_vector),chunks_vectors[i]["text"]))

    if len(scores)==0:
        raise ValueError("计算相似度列表为空")
    
    scores.sort(reverse=True)
    # print(len(scores))

    b_list=[]
    for i in range(0,top_k):
        b_list.append(scores[i][1])

    return b_list





def ask(question,history):
    
    with open(restore_path,"r",encoding="utf-8") as f:
        text_vectors=f.read()

    text_vectors=json.loads(text_vectors)
    #list[{"text","vector":list[]}]
    question_vector=get_embedding(question)
    #list[float]
    knowledge=retrieve(question_vector,text_vectors)
    # print(knowledge)
    answer=llm.LLM(question,knowledge,history)
    return answer


if __name__=="__main__":

    answer=ask(input("欢迎使用hhf智能体搜索，请输入你的问题："))
    print(answer)

