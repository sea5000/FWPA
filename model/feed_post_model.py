from datetime import datetime
from bson import ObjectId
from .mongo import get_db


def _to_str_id(doc):
    if not doc:
        return doc
    doc["_id"] = str(doc["_id"]) if isinstance(doc.get("_id"), ObjectId) else doc.get("_id")
    return doc


def list_posts():
    db = get_db()
    posts = [
        _to_str_id(p) for p in db.posts.find().sort('timestamp', -1)
    ]
    return posts


def get_post(post_id: str):
    db = get_db()
    try:
        obj_id = ObjectId(post_id)
    except Exception:
        return None
    post = db.posts.find_one({"_id": obj_id})
    return _to_str_id(post) if post else None


def create_post(author: str, text: str = "", image: str | None = None):
    db = get_db()
    data = {
        "author": author,
        "text": text or "",
        "image": image,
        "likes": 0,
        "views": 0,
        "comments": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
    result = db.posts.insert_one(data)
    return str(result.inserted_id)


def like_post(post_id: str) -> bool:
    db = get_db()
    try:
        obj_id = ObjectId(post_id)
    except Exception:
        return False
    res = db.posts.update_one({"_id": obj_id}, {"$inc": {"likes": 1}})
    return res.matched_count > 0


def add_comment(post_id: str, author: str, text: str) -> bool:
    db = get_db()
    try:
        obj_id = ObjectId(post_id)
    except Exception:
        return False
    comment = {
        "author": author,
        "text": text,
        "timestamp": datetime.utcnow().isoformat(),
    }
    res = db.posts.update_one({"_id": obj_id}, {"$push": {"comments": comment}})
    return res.matched_count > 0
