import pytest
from src.project_to_modify.transaction_service import PaymentProcessor, Transaction


def test_process_refund_zero_amount():
    processor = PaymentProcessor()
    processor.add_transaction("tx1", 100)
    result = processor.process_refund("tx1", 0)
    assert result == "ERROR: Refund amount must be greater than zero"


def test_process_refund_zero_transaction_amount():
    processor = PaymentProcessor()
    processor.add_transaction("tx1", 0)
    result = processor.process_refund("tx1", 10)
    assert result == "ERROR: Cannot process refund for zero amount"


def test_process_refund_zero_transaction_and_zero_refund():
    processor = PaymentProcessor()
    processor.add_transaction("tx1", 0)
    result = processor.process_refund("tx1", 0)
    assert result == "ERROR: Cannot process refund for zero amount"


def test_apply_discount_none():
    processor = PaymentProcessor()
    with pytest.raises(ValueError):
        processor.apply_discount(100, None)


def test_apply_discount_negative():
    processor = PaymentProcessor()
    with pytest.raises(ValueError):
        processor.apply_discount(100, -10)


def test_apply_discount_over_100():
    processor = PaymentProcessor()
    with pytest.raises(ValueError):
        processor.apply_discount(100, 110)


def test_process_refund_non_existent_transaction_zero_amount():
    processor = PaymentProcessor()
    result = processor.process_refund("non_existent", 0)
    assert result == "ERROR: Transaction not found"


def test_process_refund_negative_amount():
    processor = PaymentProcessor()
    processor.add_transaction("tx1", 100)
    result = processor.process_refund("tx1", -10)
    assert result == "ERROR: Refund amount must be greater than zero"


def test_process_refund_exceeds_amount():
    processor = PaymentProcessor()
    processor.add_transaction("tx1", 100)
    result = processor.process_refund("tx1", 150)
    assert result == "ERROR: Refund exceeds original amount"


def test_apply_discount_zero():
    processor = PaymentProcessor()
    result = processor.apply_discount(100, 0)
    assert result == 100


def test_apply_discount_50_percent():
    processor = PaymentProcessor()
    result = processor.apply_discount(100, 50)
    assert result == 50


def test_apply_discount_100_percent():
    processor = PaymentProcessor()
    result = processor.apply_discount(100, 100)
    assert result == 0


def test_apply_discount_fractional():
    processor = PaymentProcessor()
    result = processor.apply_discount(100, 25.5)
    assert result == 74.5


def test_process_refund_success():
    processor = PaymentProcessor()
    processor.add_transaction("tx1", 100)
    result = processor.process_refund("tx1", 50)
    assert result == "SUCCESS: Refund ratio 0.50 processed"


def test_process_refund_full_amount():
    processor = PaymentProcessor()
    processor.add_transaction("tx1", 100)
    result = processor.process_refund("tx1", 100)
    assert result == "SUCCESS: Refund ratio 1.00 processed"


def test_apply_discount_negative_amount():
    processor = PaymentProcessor()
    with pytest.raises(ValueError):
        processor.apply_discount(-100, 10)


def test_apply_discount_zero_amount():
    processor = PaymentProcessor()
    result = processor.apply_discount(0, 10)
    assert result == 0


def test_process_refund_transaction_not_completed():
    processor = PaymentProcessor()
    processor.add_transaction("tx1", 100)
    result = processor.process_refund("tx1", 50)
    assert result == "SUCCESS: Refund ratio 0.50 processed"
    # Повторная попытка возврата должна провалиться
    result = processor.process_refund("tx1", 50)
    assert result == "ERROR: Refund exceeds original amount"