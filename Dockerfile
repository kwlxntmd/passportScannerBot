FROM python:3.9.6

WORKDIR /app

COPY . /app

COPY passport_photos /data/passport_photos
COPY user_documents /data/user_documents
COPY passport_data.db /data/passport_data.db

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install -r requirements.txt

VOLUME /data

CMD ["python", "./passportscanbot.py"]
