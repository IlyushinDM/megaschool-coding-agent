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


def test_calculate_final_amount_with_tax():
    processor = PaymentProcessor(tax_rate=0.20)
    amount = 100
    result = processor.calculate_final_amount(amount, is_exempt=False)
    assert result == 120.0


def test_calculate_final_amount_exempt():
    processor = PaymentProcessor(tax_rate=0.20)
    amount = 100
    result = processor.calculate_final_amount(amount, is_exempt=True)
    assert result == 100.0


def test_calculate_final_amount_zero_amount():
    processor = PaymentProcessor(tax_rate=0.20)
    amount = 0
    result = processor.calculate_final_amount(amount, is_exempt=False)
    assert result == 0.0


def test_calculate_final_amount_negative_amount():
    processor = PaymentProcessor(tax_rate=0.20)
    amount = -50
    with pytest.raises(ValueError):
        processor.calculate_final_amount(amount, is_exempt=False)