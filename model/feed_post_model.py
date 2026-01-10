"""Feed Post Model - Manages social media posts in MongoDB.

This module handles CRUD operations for social feed posts, including:
- Creating new posts with text and/or images
- Retrieving posts individually or in lists
- Liking posts (incrementing like count)
- Adding comments to posts

All MongoDB ObjectId values are converted to strings for JSON serialization.
"""

from datetime import datetime
from bson import ObjectId
from .mongo import get_db

_db = get_db()
_posts_col = _db.posts
_interactions_col = _db.interactions


def _to_str_id(doc):
    """Convert MongoDB ObjectId to string for JSON response.
    
    MongoDB stores documents with an _id field as ObjectId (binary format),
    but JSON cannot serialize ObjectId directly. This helper converts it to a string.
    
    Args:
        doc: A MongoDB document (dict) or None
        
    Returns:
        The same document with _id converted to string, or None if doc is None
    """
    if not doc:
        return doc
    doc["_id"] = str(doc["_id"]) if isinstance(doc.get("_id"), ObjectId) else doc.get("_id")
    return doc


def list_posts():
    """Retrieve all posts from the database, sorted by newest first.
    
    Returns:
        List of post dictionaries with string IDs, sorted by timestamp (newest first)
    """
    posts = [_to_str_id(p) for p in _posts_col.find().sort('timestamp', -1)]
    for p in posts:
        _attach_interactions(p)
    return posts


def get_post(post_id: str):
    """Retrieve a single post by its ID.
    
    Args:
        post_id: String representation of MongoDB ObjectId
        
    Returns:
        Post dictionary with string ID if found, None otherwise
        
    Raises silently on invalid ObjectId format (returns None instead)
    """
    try:
        # Convert string ID to MongoDB ObjectId for database query
        obj_id = ObjectId(post_id)
    except Exception:
        # If the string is not a valid ObjectId format, return None
        return None
    post = _posts_col.find_one({"_id": obj_id})
    post = _to_str_id(post) if post else None
    if post:
        _attach_interactions(post)
    return post


def create_post(author: str, text: str = "", image: str | None = None):
    """Create a new post in the feed.
    
    Args:
        author: Username of the post creator
        text: Post content text (optional)
        image: Image data URL or file path (optional)
        
    Returns:
        String ID of the newly created post
    
    The new post starts with 0 likes, 0 views, and an empty comments array.
    Timestamp is set to UTC current time in ISO format.
    """
    data = {
        "author": author,
        "text": text or "",
        "image": image,
        "views": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }
    result = _posts_col.insert_one(data)
    post_id = str(result.inserted_id)
    _interactions_col.insert_one({
        'entity_type': 'post',
        'entity_id': post_id,
        'likes': [],
        'comments': [],
    })
    return post_id


def like_post(post_id: str, username: str) -> bool:
    """Add a like entry for a post in the interactions collection."""
    if not username:
        return False
    try:
        obj_id = ObjectId(post_id)
    except Exception:
        return False

    if not _posts_col.find_one({'_id': obj_id}):
        return False

    _interactions_col.update_one(
        {'entity_type': 'post', 'entity_id': post_id},
        {'$addToSet': {'likes': username}},
        upsert=True,
    )
    return True


def add_comment(post_id: str, author: str, text: str) -> bool:
    """Add a comment to a post via the interactions collection."""
    try:
        obj_id = ObjectId(post_id)
    except Exception:
        return False

    if not _posts_col.find_one({'_id': obj_id}):
        return False

    comment = {
        "author": author,
        "text": text,
        "timestamp": datetime.utcnow().isoformat(),
    }
    _interactions_col.update_one(
        {'entity_type': 'post', 'entity_id': post_id},
        {'$push': {'comments': comment}, '$setOnInsert': {'likes': []}},
        upsert=True,
    )
    return True


def _attach_interactions(doc: dict) -> None:
    """Attach likes count and comments from interactions collection to a post document."""
    if not doc:
        return
    iid = str(doc.get('_id')) if doc.get('_id') else doc.get('id')
    interactions = _interactions_col.find_one({'entity_type': 'post', 'entity_id': iid}) or {}
    likes = interactions.get('likes') or []
    doc['likes'] = len(likes)
    doc['liked_by'] = likes
    doc['comments'] = interactions.get('comments') or []
