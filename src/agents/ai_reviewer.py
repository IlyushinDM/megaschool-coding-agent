import os
import sys
import argparse
import re
from typing import Dict, Any

from github import Github, Repository, PullRequest

from src.config import settings
from src.llm_client import LLMService
from src.logger import get_logger, configure_logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

log = get_logger(__name__)

class ReviewerAgent:
    SYSTEM_PROMPT = """
    Ты — Senior Python Developer. Проведи Code Review PR.
    
    1. Ищи баги, проблемы безопасности и "плохой код".
    2. Если тесты (pytest) в CI упали — статус CHANGES_REQUESTED.
    3. Будь краток и конструктивен.
    
    Ответ строго JSON:
    {
      "status": "APPROVED" | "CHANGES_REQUESTED",
      "summary": "Резюме на русском",
      "review_details": [{"file_path": "...", "line_number": int, "comment": "..."}]
    }
    """

    def __init__(self, pr_number: int):
        self.gh = Github(settings.GITHUB_TOKEN)
        self.repo: Repository.Repository = self.gh.get_repo(settings.REPO_NAME)
        self.pr: PullRequest.PullRequest = self.repo.get_pull(pr_number)
        self.llm = LLMService()

    def _get_context(self) -> str:
        """Агрегирует данные для промпта."""
        log.info(f"Сбор данных для PR #{self.pr.number}...")
        
        diff = ""
        for file in self.pr.get_files():
            patch = file.patch or "[Binary/Large]"
            diff += f"File: {file.filename}\n```diff\n{patch}\n```\n\n"

        ci_status = "CI Results: Not found."
        # Нужна бы проверка статусов GitHub Actions
        # Для совместимости с исходным кодом читаем файл
        try:
            with open("ci_results.txt", "r", encoding="utf-8") as f:
                ci_status = f.read()
        except FileNotFoundError:
            pass

        return f"""
        TITLE: {self.pr.title}
        BODY: {self.pr.body}
        CI STATUS: {ci_status}
        
        DIFF:
        {diff[:20000]} 
        """ # Лимит токенов — это разумно, не правда ли?)

    def _publish_review(self, review: Dict[str, Any]):
        """Публикует комментарий и ставит лейблы."""
        body = f"## AI Review\n\n{review.get('summary')}\n\n"
        
        for item in review.get("review_details", []):
            line_info = f" (line {item['line_number']})" if item.get('line_number') else ""
            body += f"- `{item.get('file_path')}`{line_info}: {item['comment']}\n"

        self.pr.create_issue_comment(body)
        
        status = review.get("status")
        labels = {l.name for l in self.pr.get_labels()}
        
        if status == "APPROVED":
            if "changes-needed" in labels: self.pr.remove_from_labels("changes-needed")
            self.pr.add_to_labels("approved")
        else:
            if "approved" in labels: self.pr.remove_from_labels("approved")
            self.pr.add_to_labels("changes-needed")
            
        log.info(f"Ревью опубликовано. Статус: {status}")

    def run(self):
        context = self._get_context()
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ]
        
        result = self.llm.generate_json(messages)
        if not result or "error" in result:
            log.error("Не удалось получить ревью от LLM.")
            return

        self._publish_review(result)

if __name__ == "__main__":
    configure_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr-number", type=int, required=True)
    args = parser.parse_args()
    
    agent = ReviewerAgent(args.pr_number)
    agent.run()
