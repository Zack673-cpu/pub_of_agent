import requests
from fastapi import HTTPException

def refresh(rt:str):
    resp=requests.post(    
        "http://localhost:8000/refresh",
        json={'refresh_token':rt},      
    )
    
    print('状态码：',resp.status_code)
    if resp.status_code==200:
        tokens=resp.json()
        refresh_token=tokens['refresh_token']
        print('refresh_token:',refresh_token)
        return 
    else :
        print(tokens['detail'])
        return 

def new_book(at:str):
    resp=requests.post(
        url="http://localhost:8000/books",
        headers={'Authorization':f'Bearer {at}'},
        json={
            'title':'test',
            'requirement':'elysia 赛高'
        },
    )
    print('状态码：',resp.status_code)
    if resp.status_code==200:
        data=resp.json()
        print(data)
        return 
    else :
        print(data['detail'])
        return

def get_new_book(at:str):
    resp=requests.get(
        url="http://localhost:8000/books",
        headers={'Authorization':f'Bearer {at}'},
        json={},
    )
    print('状态码：',resp.status_code)
    if resp.status_code==200:
        data=resp.json()
        print(data)
        return data['books'][0]['id']
    else:
        print(data['detail'])
        return 

def get_book_byid(at:str,book_id):
    resp=requests.get(
        url=f"http://localhost:8000/books/{book_id}",
        headers={'Authorization':f'Bearer {at}'},
        json={},
    )
    print('状态码：',resp.status_code)
    if resp.status_code==200:
        data=resp.json()
        print(data) 
        return data['id']
    else:
        print(data['detail'])
        return 


if __name__ =="__main__":
    login_resp=requests.post(
        "http://localhost:8000/login",
        json={'username':'elysia','password':'jerry1010'}

    )

    tokens=login_resp.json()
    refresh_token=tokens['refresh_token']
    access_token=tokens['access_token']
    # refresh(refresh_token)
    # refresh(refresh_token)
    # new_book(access_token)
    book_id=get_new_book(access_token)
    get_book_byid(access_token,book_id)