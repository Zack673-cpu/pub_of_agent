import requests

url="http://localhost:8000/ask"
headers={"authorization":"123456"}

# 情况一：不带头
# 情况二：headers = {"Authorization": "错误值"}
# 情况三：headers = {"Authorization": "123456"}

body={"Question":"什么是线性代数"}


response=requests.post(url,json=body,headers=headers)
print(response.status_code)
print(response.json())
