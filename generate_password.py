import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

password = "123456"  # 你想设置的密码
hashed_password = hash_password(password)
print(f"\n生成的密码哈希值：\n{hashed_password}") 