from encryption_util import encrypt_password
import json

# 평문 비밀번호 입력
plain_pw = input("관리자 비밀번호 입력: ")
encrypted_pw = encrypt_password(plain_pw)

# 저장
config = {
    "admin_password": encrypted_pw
}

with open("admin_config.json", "w") as f:
    json.dump(config, f)

print("✅ admin_config.json 생성 완료!")