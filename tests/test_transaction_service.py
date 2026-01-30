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


def test_process_refund_already_processed():
    processor = PaymentProcessor()
    processor.add_transaction("tx1", 100)
    processor.process_refund("tx1", 50)
    result = processor.process_refund("tx1", 50)
    assert result == "ERROR: Transaction already processed"


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