
import os
import requests
from dotenv import load_dotenv
load_dotenv() 

# history[(用户问题，ai回答)]
def LLM(question,knowledge:list,history:list) -> str :
    key = os.getenv("DASHSCOPE_API_KEY")
    if key is None: raise ValueError(r"api key获取出错，检查pub_of_agent\.env")

    
    
    messages=[{"role": "system", "content": "根据参考资料仔细思考，不懂就直说不懂"}]
    for u,a in history:
        messages.append({"role":"user","content":u})
        messages.append({"role":"assistant","content":a})

    messages.append({"role":"user","content":f"本轮问题：{question}\n参考资料：{knowledge}"})

    url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers={
        "Authorization": "Bearer " + key,   # 鉴权
        "Content-Type": "application/json"
    }
    body={
        "model": "qwen-plus",
        "messages": messages,
        "temperature":0.5,
        "repetition_penalty":1.2

    }

    request=requests.post(url,headers=headers,json=body)
    request=request.json()
    return request["choices"][0]["message"]["content"]






