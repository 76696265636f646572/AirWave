from app.db.models import QueueStatus
from app.db.repository import NewQueueItem, Repository


def test_queue_ordering_and_reorder(tmp_path):
    db_url = f"sqlite+pysqlite:///{tmp_path}/repo.db"
    repo = Repository(db_url)
    repo.init_db()

    created = repo.enqueue_items(
        [
            NewQueueItem(source_url="u1", normalized_url="u1", source_type="video", title="a"),
            NewQueueItem(source_url="u2", normalized_url="u2", source_type="video", title="b"),
            NewQueueItem(source_url="u3", normalized_url="u3", source_type="video", title="c"),
        ]
    )
    assert [x.queue_position for x in created] == [1, 2, 3]

    assert repo.reorder_item(created[2].id, 0) is True
    queue = repo.list_queue()
    assert [x.title for x in queue if x.status == QueueStatus.queued] == ["c", "a", "b"]

    next_item = repo.dequeue_next()
    assert next_item is not None
    assert next_item.title == "c"
    assert next_item.status == QueueStatus.playing
