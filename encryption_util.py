import os
from cryptography.fernet import Fernet
import json

KEY_PATH = "secret.key"

# 암호 키 파일 생성
def generate_key():
    print("generate_key")
    """키 파일이 없으면 새로 생성"""
    if not os.path.exists(KEY_PATH):
        key = Fernet.generate_key()
        with open(KEY_PATH, "wb") as f:
            f.write(key)
        print("🔑 키 파일 생성 완료")

# 암호키 불러오기
def load_key():
    print("load_key")
    return open(KEY_PATH, "rb").read()

# 비밀번호 암호화
def encrypt_password(password: str) -> str:
    print("encrypt_password")
    return Fernet(load_key()).encrypt(password.encode()).decode()

# 비밀번호 복호화
def decrypt_password(encrypted: str) -> str:
    print("decrypt_password")
    return Fernet(load_key()).decrypt(encrypted.encode()).decode()

# 관리자 비밀번호 확인    
def get_admin_password():
    print("get_admin_password")
    with open("admin_config.json", "r") as f:
        data = json.load(f)
    encrypted_pw = data["admin_password"]
    return decrypt_password(encrypted_pw)

# import 시 자동으로 키 생성
generate_key()