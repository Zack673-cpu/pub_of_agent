import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
JwtSecret=os.getenv("JWT_SECRET")


# ---- 1. 用户登录验证的密码工具 ----
def hash_password(plain: str) -> str:
    """输入明文密码 → 输出 bcrypt 哈希串（注册时存库）"""
    if plain is None:
        raise ValueError("密码不能为 None")

    plain_b=plain.encode("utf-8")
    #转二进制
    salt=bcrypt.gensalt()
    #生成随机盐
    plain_hash=bcrypt.hashpw(plain_b,salt)
    #哈希，bytes类型
    #内容=算法标识 + 成本 + 盐 + 实际哈希
    return plain_hash.decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    """登录时核对：明文 vs 库里存的哈希 → 是否匹配"""
    if plain is None or hashed is None:
        return False
    try:

        plain_b=plain.encode("utf-8")
        hashed_b = hashed.encode("utf-8")
        return bcrypt.checkpw(plain_b, hashed_b)
        
    except (ValueError,TypeError):
        return False




# ---- 2. Access token（JWT）----
def create_access_token(user_id: int) -> str:
    """签发：把 user_id 写进载荷 + 设置过期时间 → 用 JWT_SECRET 签名 → 返回 token 串"""
    now=datetime.now(timezone.utc)
    time=datetime.now(timezone.utc)+timedelta(minutes=30)

    exp_time=int(time.timestamp())
    now_time=int(now.timestamp())
    # .timestamp() 会把这个时间点转换成 Unix 时间戳，返回一个浮点数，例如 1789321800.0。
    # 但是jwt要求整数，所以还要再转一下
    payload={"user_id":user_id,"iat":now_time,"exp":exp_time}
    key=JwtSecret
    token=jwt.encode(payload, key, algorithm="HS256") 
    return token

def verify_access_token(token: str) -> int:
    """验签：校验签名和过期 → 返回载荷里的 user_id；不合法抛异常"""
    try:

        payload=jwt.decode(token,JwtSecret, algorithms=["HS256"])
        return payload["user_id"]
    except (jwt.ExpiredSignatureError,jwt.InvalidTokenError) as e:
        raise ValueError(f" JWT鉴权失败，原因：{e}")







    