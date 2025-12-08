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
    db = get_db()
    # Query all posts and sort by timestamp in descending order (-1 = descending)
    posts = [
        _to_str_id(p) for p in db.posts.find().sort('timestamp', -1)
    ]
    return posts


def get_post(post_id: str):
    """Retrieve a single post by its ID.
    
    Args:
        post_id: String representation of MongoDB ObjectId
        
    Returns:
        Post dictionary with string ID if found, None otherwise
        
    Raises silently on invalid ObjectId format (returns None instead)
    """
    db = get_db()
    try:
        # Convert string ID to MongoDB ObjectId for database query
        obj_id = ObjectId(post_id)
    except Exception:
        # If the string is not a valid ObjectId format, return None
        return None
    post = db.posts.find_one({"_id": obj_id})
    return _to_str_id(post) if post else None


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
    db = get_db()
    # Prepare the document to insert into MongoDB
    data = {
        "author": author,
        "text": text or "",  # Use empty string if no text provided
        "image": image,  # Can be None if no image
        "likes": 0,  # Start with zero likes
        "views": 0,  # Start with zero views
        "comments": [],  # Empty array for comments
        "timestamp": datetime.utcnow().isoformat(),  # ISO format: "2025-12-08T14:30:45.123456"
    }
    result = db.posts.insert_one(data)
    return str(result.inserted_id)  # Return the ID of the newly inserted document


def like_post(post_id: str) -> bool:
    """Increment the like count on a post by 1.
    
    Uses MongoDB's $inc operator to atomically increment the likes field.
    This is thread-safe and prevents race conditions.
    
    Args:
        post_id: String ID of the post to like
        
    Returns:
        True if post was found and updated, False otherwise
    """
    db = get_db()
    try:
        obj_id = ObjectId(post_id)
    except Exception:
        # Invalid ObjectId format
        return False
    # $inc: MongoDB operator to increment a numeric field
    # Example: {"$inc": {"likes": 1}} increases 'likes' by 1
    res = db.posts.update_one({"_id": obj_id}, {"$inc": {"likes": 1}})
    # matched_count > 0 means the document was found and updated
    return res.matched_count > 0


def add_comment(post_id: str, author: str, text: str) -> bool:
    """Add a comment to a post.
    
    Uses MongoDB's $push operator to append a comment to the comments array.
    
    Args:
        post_id: String ID of the post to comment on
        author: Username of the person commenting
        text: The comment text
        
    Returns:
        True if comment was added, False if post not found
    """
    db = get_db()
    try:
        obj_id = ObjectId(post_id)
    except Exception:
        return False
    # Create comment object with author, text, and timestamp
    comment = {
        "author": author,
        "text": text,
        "timestamp": datetime.utcnow().isoformat(),
    }
    # $push: MongoDB operator to append element to array field
    # Example: {"$push": {"comments": {...}}} adds comment to comments array
    res = db.posts.update_one({"_id": obj_id}, {"$push": {"comments": comment}})
    return res.matched_count > 0
