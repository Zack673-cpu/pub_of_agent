import requests
from fastapi import HTTPException

def refresh(rt:str):
    resp=requests.post(    
        "http://localhost:8000/refresh",
        json={'refresh_token':rt},      
    )
    
    print('refresh 状态码：',resp.status_code)
    data=resp.json()
    if resp.status_code==200:
        print('refresh',data) 
    else:
        if 'detail' in data:
            print('refresh',data['detail'])
        else :
            print('refresh',data)
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
    print('new_book 状态码：',resp.status_code)
    data=resp.json()
    if resp.status_code==200:
        print('new_book',data) 
    else:
        if 'detail' in data:
            print('new_book',data['detail'])
        else :
            print('new_book',data)
    return 

def get_new_book(at:str):
    resp=requests.get(
        url="http://localhost:8000/books",
        headers={'Authorization':f'Bearer {at}'},
    )
    print('get_new_book 状态码：',resp.status_code)
    data=resp.json()
    if resp.status_code==200:
        print('get_new_book',data)
        return data['books'][0]['id']
    else:
        if 'detail' in data:
            print('get_new_book',data['detail'])
        else: print('get_new_book',data)
        return 

def get_book_byid(at:str,book_id):
    resp=requests.get(
        url=f"http://localhost:8000/books/{book_id}",
        headers={'Authorization':f'Bearer {at}'},
    )
    print('get_book_byid 状态码：',resp.status_code)        
    data=resp.json()
    if resp.status_code==200:
        print('get_book_byid',data) 
        return data['id']
    else:
        if 'detail' in data:
            print('get_book_byid',data['detail'])
        else: print('get_book_byid',data)
        return 

def put_outline_staging(at:str,book_id=1):
    resp=requests.put(
        url=f"http://localhost:8000/books/{book_id}/outline/staging",
        headers={'Authorization':f'Bearer {at}'},
        json={"test":'test'},
    )
    print('put_outline_staging 状态码：',resp.status_code)
    data=resp.json()
    if resp.status_code==200:
        print('put_outline_staging',data) 
    else:
        if 'detail' in data:
            print('put_outline_staging',data['detail'])
        else :
            print('put_outline_staging',data)
    return 

def get_outline_versions(at:str,book_id=1):
    resp=requests.get(
        url=f"http://localhost:8000/books/{book_id}/outline/versions",
        headers={'Authorization':f'Bearer {at}'},
    )
    print('get_outline_versions 状态码：',resp.status_code)
    data=resp.json()
    if resp.status_code==200:
        print('get_outline_versions',data) 
    else:
        if 'detail' in data:
            print('get_outline_versions',data['detail'])
        else :
            print('get_outline_versions',data)
    return 

def put_section_staging(at:str,section_id):
    resp=requests.put(
        url=f"http://localhost:8000/sections/{section_id}/staging",
        headers={'Authorization':f'Bearer {at}'},
        json={'content':'test01'}
    )
    print('put_section_staging 状态码：',resp.status_code)
    data=resp.json()
    if resp.status_code==200:
        print('put_section_staging',data) 
    else:
        if 'detail' in data:
            print('put_section_staging',data['detail'])
        else :
            print('put_section_staging',data)
    return 

def get_section_versions(at:str,section_id):
    resp=requests.get(
        url=f"http://localhost:8000/sections/{section_id}/versions",
        headers={'Authorization':f'Bearer {at}'},
    )
    print('get_section_versions 状态码：',resp.status_code)
    data=resp.json()
    if resp.status_code==200:
        print('get_section_versions',data) 
    else:
        if 'detail' in data:
            print('get_section_versions',data['detail'])
        else :
            print('get_section_versions',data)
    return 

if __name__ =="__main__":
    login_resp=requests.post(
        "http://localhost:8000/login",
        json={'username':'elysia','password':'jerry1010'}

    )

    tokens=login_resp.json()
    refresh_token=tokens['refresh_token']
    access_token=tokens['access_token']
    refresh(refresh_token)
    refresh(refresh_token)
    new_book(access_token)
    book_id=get_new_book(access_token)
    get_book_byid(access_token,book_id)
    put_outline_staging(access_token)
    get_outline_versions(access_token)

    for i in range (1,4):
        get_section_versions(access_token,i)
    get_section_versions(access_token,999)

    put_section_staging(access_token,1)
