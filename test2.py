import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

print("EMAIL_ADDRESS:", EMAIL_ADDRESS)
print("EMAIL_PASSWORD 설정됨:", bool(EMAIL_PASSWORD))

server = smtplib.SMTP("smtp.gmail.com", 587)

print("1. SMTP 연결 성공")

server.starttls()

print("2. TLS 연결 성공")

server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

print("3. Gmail 로그인 성공")

server.quit()