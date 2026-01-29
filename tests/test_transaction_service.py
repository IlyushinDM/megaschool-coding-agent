import pytest
from src.project_to_modify.transaction_service import PaymentProcessor


def test_process_refund_with_zero_amount():
    processor = PaymentProcessor()
    processor.add_transaction('tx1', 100)
    result = processor.process_refund('tx1', 0)
    assert result == "ERROR: Refund amount must be greater than zero"


def test_process_refund_with_negative_amount():
    processor = PaymentProcessor()
    processor.add_transaction('tx2', 100)
    result = processor.process_refund('tx2', -50)
    assert result == "ERROR: Refund amount must be greater than zero"


def test_apply_discount_with_negative_value():
    processor = PaymentProcessor()
    with pytest.raises(ValueError, match='Скидка не может быть отрицательной'):
        processor.apply_discount(100, -10)


def test_apply_discount_above_100_percent():
    processor = PaymentProcessor()
    with pytest.raises(ValueError, match='Скидка не может превышать 100%'):
        processor.apply_discount(100, 110)
