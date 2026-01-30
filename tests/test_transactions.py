import pytest
from src.project_to_modify.transaction_service import PaymentProcessor

@pytest.fixture
def processor():
    return PaymentProcessor(tax_rate=0.20)

def test_calculate_total_with_tax(processor):
    assert processor.calculate_total_with_tax(100) == 120.0
    with pytest.raises(ValueError):
        processor.calculate_total_with_tax(-1)

def test_apply_discount(processor):
    assert processor.apply_discount(100, 10) == 90.0
    with pytest.raises(ValueError, match="превышать 100%"):
        processor.apply_discount(100, 110)

def test_process_refund_success(processor):
    processor.add_transaction("TX123", 100.0)
    result = processor.process_refund("TX123", 50.0)
    assert "SUCCESS" in result
    assert processor.transactions["TX123"].status == "REFUNDED"

def test_process_refund_not_found(processor):
    result = processor.process_refund("NON_EXISTENT", 10.0)
    assert "ERROR" in result

def test_process_refund_zero_division(processor):
    """
    ПРОВОКАЦИЯ БАГА:
    Тест проверяет транзакцию с нулевой суммой. 
    Сейчас код упадет с ZeroDivisionError. Агент должен это исправить.
    """
    processor.add_transaction("TX_ZERO", 0.0)
    try:
        result = processor.process_refund("TX_ZERO", 0.0)
        assert "ERROR" in result or "SUCCESS" in result
    except ZeroDivisionError:
        pytest.fail("Код упал с ZeroDivisionError! Агент должен это исправить.")
