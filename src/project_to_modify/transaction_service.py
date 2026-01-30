from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Transaction:
    id: str
    amount: float
    currency: str
    status: str  # PENDING, COMPLETED, FAILED
    timestamp: datetime


class PaymentProcessor:
    """
    Продуктовый сервис для обработки платежей.
    Содержит скрытые баги для проверки работы AI-агента.
    """
    
    def __init__(self, tax_rate: float = 0.20):
        self.tax_rate = tax_rate
        self.transactions: Dict[str, Transaction] = {}

    def calculate_total_with_tax(self, amount: float) -> float:
        """
        Вычисляет итоговую сумму с учетом налогов.
        """
        if amount < 0:
            raise ValueError("Сумма не может быть отрицательной")
        return amount * (1 + self.tax_rate)

    def apply_discount(self, amount: float, discount_percent: float) -> float:
        """
        Применяет скидку к сумме.
        """
        if discount_percent is None:
            raise ValueError("Discount percent must be provided")
        if discount_percent < 0:
            raise ValueError("Скидка не может быть отрицательной")
        if discount_percent > 100:
            raise ValueError("Скидка не может превышать 100%")
        return amount - (amount * (discount_percent / 100))

    def process_refund(self, transaction_id: str, refund_amount: float) -> str:
        """
        Оформляет возврат по транзакции.
        """
        if transaction_id not in self.transactions:
            return "ERROR: Transaction not found"
        
        transaction = self.transactions[transaction_id]
        
        # Проверяем сумму транзакции на 0 в начале
        if transaction.amount == 0:
            return "ERROR: Cannot process refund for zero amount"
        
        if refund_amount <= 0:
            return "ERROR: Refund amount must be greater than zero"
        
        if refund_amount > transaction.amount:
            return "ERROR: Refund exceeds original amount"
        
        # Обновляем статус транзакции только если возврат успешно обработан
        if refund_amount <= transaction.amount:
            transaction.status = "REFUNDED"
        
        ratio = refund_amount / transaction.amount
        return f"SUCCESS: Refund ratio {ratio:.2f} processed"

    def add_transaction(self, t_id: str, amount: float, currency: str = "USD"):
        """
        Добавляет транзакцию в базу.
        """
        self.transactions[t_id] = Transaction(
            id=t_id,
            amount=amount,
            currency=currency,
            status="PENDING",
            timestamp=datetime.now()
        )