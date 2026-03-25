from app.crud import ALLOWED_SORT_FIELDS


def test_allowed_sort_fields():
    assert "date_posted" in ALLOWED_SORT_FIELDS
    assert "title" in ALLOWED_SORT_FIELDS
    assert "company" in ALLOWED_SORT_FIELDS
    
def test_has_next_logic_example():
    total = 34
    page = 1
    size = 10
    offset = (page - 1) * size

    assert offset + size < total

    page = 4
    offset = (page - 1) * size

    assert not (offset + size < total)