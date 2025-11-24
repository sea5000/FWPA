from .mongo import get_db


def upload_note(author: str, data: dict) -> str:
    db = get_db()
    payload = dict(data or {})
    payload['author'] = author
    payload['views'] = 0
    result = db.notes.insert_one(payload)
    return str(result.inserted_id)


def view_note(title: str) -> dict | None:
    db = get_db()
    note = db.notes.find_one({'title': title})
    if not note:
        return None
    db.notes.update_one({'_id': note['_id']}, {'$inc': {'views': 1}})
    note['_id'] = str(note['_id'])
    return note
