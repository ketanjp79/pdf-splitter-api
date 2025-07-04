from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from celery.result import AsyncResult
from worker import split_pdf_from_drive_task
import uuid
import os
import json

app = FastAPI()


@app.post("/split/drive")
async def split_drive(file_id: str = Form(...), prefixes: str = Form("")):
    task_id = str(uuid.uuid4())
    task = split_pdf_from_drive_task.apply_async(args=[file_id, prefixes, task_id])
    return {"status": "queued", "task_id": task.id}

@app.get("/result/{task_id}")
def get_result(task_id: str):
    result_file = f"results/{task_id}.json"
    if os.path.exists(result_file):
        with open(result_file, "r") as f:
            return json.load(f)
    return {"status": "processing"}
app.mount("/", StaticFiles(directory="static", html=True), name="static")
