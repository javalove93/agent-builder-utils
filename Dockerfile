# Python 3.12 기반
# src 폴더를 /app 폴더로 복사
# python -m pip install -r /app/requirements.txt 명령어 실행
# 실행 경로는 /app
FROM python:3.12
COPY src /app
WORKDIR /app
RUN python -m pip install -r requirements.txt
CMD ["python", "app.py"]