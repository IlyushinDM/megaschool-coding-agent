from fastapi import FastAPI, BackgroundTasks, Request
from src.agents.code_agent import DeveloperAgent
from src.logger import log

app = FastAPI()

def run_agent_process(issue_number: int):
    """Фоновая задача для запуска агента."""
    try:
        log.info(f"[Webhook] Запуск обработки Issue #{issue_number}")
        agent = DeveloperAgent()
        agent.run(issue_number)
    except Exception as e:
        log.error(f"Ошибка в фоновом процессе агента: {e}")

@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Эндпоинт для GitHub Webhooks."""
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}

    action = payload.get("action")
    
    # Реакция на открытие Issue
    if action == "opened" and "issue" in payload:
        issue_number = payload["issue"]["number"]
        background_tasks.add_task(run_agent_process, issue_number)
        return {"status": "accepted", "message": f"Agent started for issue #{issue_number}"}
    
    # Реагируем на комментарии (Re-run)
    if action == "created" and "comment" in payload and "issue" in payload:
        comment_body = payload["comment"]["body"]
        if "AI Code Review" in comment_body: # Если это ревью от бота
             #? Здесь можно добавить логику парсинга, но для простоты перезапускаем
             pass

    return {"status": "ignored", "reason": f"Action '{action}' not supported"}

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
