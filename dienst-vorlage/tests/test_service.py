import pytest
from app.application.ports import ItemRepository
from app.application.services import ItemService
from app.domain.errors import InvalidInput, NotFound


class InMemoryRepo(ItemRepository):
    def __init__(self): self.d = {}
    def list(self, subject_id=None): return [i for i in self.d.values() if subject_id in (None, i.subject_id)]
    def get(self, i): return self.d.get(i)
    def save(self, item): self.d[item.id] = item
    def delete(self, i): self.d.pop(i, None)
    def delete_subject(self, s): self.d = {k: i for k, i in self.d.items() if i.subject_id != s}


@pytest.fixture
def svc():
    return ItemService(InMemoryRepo())


def test_add_list_delete(svc):
    a = svc.add_item("f", " Erstes ")
    svc.add_item("anderes", "Zweites")
    assert [i.text for i in svc.list_items("f")] == ["Erstes"]
    svc.delete_item(a.id)
    with pytest.raises(NotFound):
        svc.delete_item(a.id)
    with pytest.raises(InvalidInput):
        svc.add_item("f", "  ")


def test_subject_hooks(svc):
    svc.add_item("f", "a")
    svc.add_item("f", "b")
    assert svc.subject_status("f") == {"count": 2}
    svc.discard_subject("f")
    assert svc.subject_status("f") == {"count": 0}
