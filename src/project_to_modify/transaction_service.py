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
        """Вычисляет итоговую сумму с учетом налогов."""
        if amount < 0:
            raise ValueError("Сумма не может быть отрицательной")
        return amount * (1 + self.tax_rate)

    def apply_discount(self, amount: float, discount_percent: float) -> float:
        """Применяет скидку к сумме."""
        # ! БАГ №1: Нет проверки, что скидка не превышает 100%
        # ! БАГ №2: Нет проверки на отрицательную скидку
        return amount - (amount * (discount_percent / 100))

    def process_refund(self, transaction_id: str, refund_amount: float) -> str:
        """Оформляет возврат по транзакции."""
        if transaction_id not in self.transactions:
            return "ERROR: Transaction not found"
        
        transaction = self.transactions[transaction_id]
        
        # ! БАГ №3: ZeroDivisionError возможен, если кто-то захочет вычислить 
        # ! коэффициент возврата от суммы транзакции, равной 0
        ratio = refund_amount / transaction.amount
        
        if refund_amount > transaction.amount:
            return "ERROR: Refund exceeds original amount"
            
        transaction.status = "REFUNDED"
        return f"SUCCESS: Refund ratio {ratio:.2f} processed"

    def add_transaction(self, t_id: str, amount: float, currency: str = "USD"):
        """Добавляет транзакцию в базу."""
        self.transactions[t_id] = Transaction(
            id=t_id,
            amount=amount,
            currency=currency,
            status="PENDING",
            timestamp=datetime.now()
        )
