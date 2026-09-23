import requests


def refresh(rt:str):
    resp=requests.post(    
        "http://localhost:8000/refresh",
        json={'refresh_token':rt},      
    )
    tokens=resp.json()
    print('状态码：',resp.status_code)
    refresh_token=tokens['refresh_token']
    print('refresh_token:',refresh_token)
    return 


if __name__ =="__main__":
    login_resp=requests.post(
        "http://localhost:8000/login",
        json={'username':'baseline_check','password':'testpass123'}

    )

    tokens=login_resp.json()
    refresh_token=tokens['refresh_token']
    refresh(refresh_token)
    refresh(refresh_token)