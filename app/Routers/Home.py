from fastapi import APIRouter, Form, UploadFile
from typing import List
import json

import asyncio
import shutil
import os

from app.Utils.Generate_reviews import start

router = APIRouter()


@router.post("/generate_reviews")
def generate_reviews(reviewCount: int = Form(...), From: str = Form(...), To: str = Form(...), rate: str = Form(...), keywords: str = Form(...), file: UploadFile = Form(...)):
    rate = json.loads(rate)
    directory = "./data"
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(f"{directory}/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return asyncio.run(start(reviewCount, rate, From, To, keywords, file.filename))
