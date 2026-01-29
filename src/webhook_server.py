from fastapi import FastAPI, Request, BackgroundTasks
import subprocess
import os

app = FastAPI()

def run_agent_task(issue_number: int):
    # Запуск агента как подпроцесса
    subprocess.run(["python", "-m", "src.agents.code_agent", "--issue-number", str(issue_number)])

@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    
    # Проверяем, что это открытие Issue
    if data.get("action") == "opened" and "issue" in data:
        issue_number = data["issue"]["number"]
        # Запускаем в фоне, чтобы GitHub не ждал долгого ответа
        background_tasks.add_task(run_agent_task, issue_number)
        return {"status": "Agent started"}
    
    return {"status": "Ignored"}
