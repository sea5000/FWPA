"""Notes Model - Manages community notes in MongoDB.

This module provides functions to create, retrieve, and manage study notes
shared in the community section. Notes can be viewed and their view count
is tracked.
"""

from .mongo import get_db


def upload_note(author: str, data: dict) -> str:
    """Create and store a new note in the database.
    
    Args:
        author: Username of the person creating the note
        data: Dictionary containing note data (title, content, subject, etc.)
              Optional fields like 'subject' can be included
        
    Returns:
        String ID of the newly created note
        
    The function adds author and views=0 to the data before insertion.
    The 'payload' pattern creates a copy of the data to avoid modifying the original.
    """
    db = get_db()
    # Create a new dictionary from the input data (shallow copy)
    # This prevents modifying the original data passed in
    payload = dict(data or {})
    # Add metadata fields
    payload['author'] = author  # Record who created the note
    payload['views'] = 0  # Initialize view counter to zero
    # Insert the complete document into the notes collection
    result = db.notes.insert_one(payload)
    # Return the MongoDB-generated ID as a string
    return str(result.inserted_id)


def view_note(title: str) -> dict | None:
    """Retrieve a note by title and increment its view count.
    
    Args:
        title: The title of the note to retrieve
        
    Returns:
        Note dictionary with string ID if found, None otherwise
        
    Side effect: Increments the 'views' field by 1 when note is accessed.
    This tracks how many times the note has been viewed.
    """
    db = get_db()
    # Query for note by title (title should be unique per user in practice)
    note = db.notes.find_one({'title': title})
    if not note:
        return None
    # Increment the views counter by 1 using MongoDB $inc operator
    # This operation is atomic and thread-safe
    db.notes.update_one({'_id': note['_id']}, {'$inc': {'views': 1}})
    # Convert MongoDB ObjectId to string for JSON serialization
    note['_id'] = str(note['_id'])
    return note
