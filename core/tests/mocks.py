from unittest.mock import MagicMock


class MockCollection:
    find = MagicMock()
    count_documents = MagicMock()
    insert_one = MagicMock()
    update_one = MagicMock()
    delete_one = MagicMock()
    insert_many = MagicMock()


class MockClient:
    add_row = MagicMock()
    delete_row = MagicMock()
    patch_row = MagicMock()
