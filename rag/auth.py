

# ---- 1. 密码工具 ----
def hash_password(plain: str) -> str:
    """输入明文密码 → 输出 bcrypt 哈希串（注册时存库）"""

def verify_password(plain: str, hashed: str) -> bool:
    """登录时核对：明文 vs 库里存的哈希 → 是否匹配"""

# ---- 2. Access token（JWT）----
def create_access_token(user_id: int) -> str:
    """签发：把 user_id 写进载荷 + 设置过期时间 → 用 JWT_SECRET 签名 → 返回 token 串"""

def verify_access_token(token: str) -> int:
    """验签：校验签名和过期 → 返回载荷里的 user_id；不合法抛异常"""









    