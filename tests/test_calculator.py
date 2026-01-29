from src.project_to_modify.calculator import add, subtract

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_subtract():
    assert subtract(10, 5) == 5
    assert subtract(2, 3) == -1
