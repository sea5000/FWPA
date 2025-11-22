from .login_model import get_user_by_username
from datetime import datetime
from pymongo import MongoClient
import os
from typing import Optional, Dict
from datetime import datetime as dt

# MongoDB setup (configurable via MONGO_URI env)
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
_client = MongoClient(MONGO_URI)
_db = _client.get_database('mydatabase')
_users_col = _db.get_collection('users')
_decks_col = _db.get_collection('decks')

#_cards_col = _db.get_collection('cards')
# ensure a unique index on username where possible (best-effort)
# try:
#     _users_col.create_index('username', unique=True)
# except Exception:
#     # don't fail import if index creation is not allowed / DB not available
#     pass
"""
Login model with hardcoded user data for teaching purposes.
No database connection required.
"""
# client = MongoClient("mongodb://localhost:27017")

# db = client["mydatabase"]
# cards = db["cards"]

def _make_card_dict(cid, front, back, tags=None, correct_count=0, incorrect_count=0, last_reviewed=None, ease=2.5, interval=0, repetitions=0):
    """Create a plain dict representing a card (no classes)."""
    return {
        'id': str(cid),
        'front': front,
        'back': back,
        'tags': list(tags) if tags else [],
        'correct_count': int(correct_count),
        'incorrect_count': int(incorrect_count),
        'last_reviewed': last_reviewed.isoformat() if last_reviewed else None,
        'ease': float(ease),
        'interval': int(interval),
        'repetitions': int(repetitions),
    }

def _make_deck_dict(did, name, summary, cards_map):
    """Create a plain dict representing a deck; cards_map values should be card dicts."""
    return {
        'id': str(did),
        'name': name,
        'summary': summary,
        'len': str(len(cards_map)),
        'cards': cards_map,
    }

# def DeckImportJSON(json):
#     decks = []
#     for deck_id, deck_data in json.items():
#         cardsFromJson = {}
#         for card_id, card_tuple in deck_data['cards'].items():
#             front, back = card_tuple
#             cardsFromJson[card_id] = _make_card_dict(card_id, front, back)
#         deck = _make_deck_dict(deck_data['id'], deck_data['name'], deck_data.get('summary',''), cardsFromJson)
#         decks.append(deck)
#     return decks

def get_deck_by_id(deck_id):
    """
    Retrieve a deck by its ID from the hardcoded decks.
    
    Args:
        deck_id (int): The ID of the deck to retrieve"""
    # Try to read from MongoDB first
    if deck_id is None:
        return None

    # normalize id to string for storage keys
    sid = str(deck_id)
    # primary source: 'decks' collection
    doc = _decks_col.find_one({'id': sid})
    if doc:
        # convert doc -> deck dict
        cards = {}
        for cid, cdoc in (doc.get('cards') or {}).items():
            try:
                last = cdoc.get('last_reviewed')
                last_dt = datetime.fromisoformat(last) if last else None
            except Exception:
                last_dt = None
            # normalize keys to strings so in-memory deck matches DB storage keys
            cards[str(cid)] = _make_card_dict(cid, cdoc.get('front'), cdoc.get('back'), tags=cdoc.get('tags', []), correct_count=cdoc.get('correct_count', 0), incorrect_count=cdoc.get('incorrect_count', 0), last_reviewed=last_dt, ease=cdoc.get('ease',2.5), interval=cdoc.get('interval',0), repetitions=cdoc.get('repetitions',0))
        deck = _make_deck_dict(doc.get('id'), doc.get('name'), doc.get('summary',''), cards)
        return deck

def get_user_study_data(username):
    """
    Retrieve study data for a given user.
    
    Args:
        username (str): The username of the user"""
    # prefer DB-backed users
    if not username:
        return None
    doc = _users_col.find_one({'username': username})
    if doc and 'studyData' in doc:
        return doc.get('studyData')

    # fallback to in-memory user
    user = get_user_by_username(username)
    if user and 'studyData' in user:
        return user['studyData']
    return None

def get_user_decks(username):
    """
    Retrieve the decks associated with a given user.
    
    Args:
        username (str): The username of the user
        
    Returns:
        list: List of deck dictionaries associated with the user
    """
    study = get_user_study_data(username)
    if not study:
        return []

    deck_ids = study.get('decks', [])
    decks = []
    for deck_id in deck_ids:
        deck = get_deck_by_id(deck_id)
        if deck:
            decks.append(deck)
    return decks

def get_deck(deck_id):
    """
    Retrieve a deck by its ID.
    
    Args:
        deck_id (int): The ID of the deck to retrieve
        
    Returns:
        dict: Deck dictionary if found, None otherwise
    """
    # Alias to get_deck_by_id which already handles DECKS list
    return get_deck_by_id(deck_id)

def update_card(deck_id, card_id, front, back):
    """Update an existing card's front/back in the in-memory deck.

    Returns True if updated, False if deck not found.
    """
    deck = get_deck_by_id(deck_id)
    if not deck:
        return False
    # normalize key to string for storage keys
    card_key = str(card_id)

    # if deck is stored in DB, update subdocument directly
    sid = str(deck_id)
    doc = _decks_col.find_one({'id': sid})
    if doc:
        update_doc = {
            f'cards.{card_key}.front': front,
            f'cards.{card_key}.back': back,
        }
        _decks_col.update_one({'id': sid}, {'$set': update_doc})
        return True

    # otherwise operate on in-memory deck dict
    cards = deck.get('cards', {})
    if card_key in cards:
        cards[card_key]['front'] = front
        cards[card_key]['back'] = back
        # update derived length
        deck['len'] = str(len(cards))
        return True

    # create new card dict and add
    new_card = _make_card_dict(card_key, front, back)
    cards[card_key] = new_card
    deck['len'] = str(len(cards))

    # persist to DB if deck document exists (double-check)
    doc = _decks_col.find_one({'id': sid})
    if doc:
        cdoc = {
            'front': new_card['front'],
            'back': new_card['back'],
            'tags': new_card['tags'],
            'correct_count': new_card['correct_count'],
            'incorrect_count': new_card['incorrect_count'],
            'last_reviewed': new_card['last_reviewed'],
            'ease': new_card['ease'],
            'interval': new_card['interval'],
            'repetitions': new_card['repetitions'],
        }
        _decks_col.update_one({'id': sid}, {'$set': {f'cards.{card_key}': cdoc, 'len': str(len(cards))}})
    return True

def add_card(deck_id, front, back):
    """Add a new card to the deck and return the new Card instance.

    The new card id tries to follow numeric indexing when existing keys are numeric.
    """
    deck = get_deck_by_id(deck_id)
    if not deck:
        return None

    cards = deck.get('cards', {})

    # determine next id (prefer numeric sequence when possible)
    numeric_keys = []
    for k in cards.keys():
        if isinstance(k, int) or (isinstance(k, str) and k.isdigit()):
            try:
                numeric_keys.append(int(k))
            except Exception:
                pass

    if numeric_keys:
        next_id = max(numeric_keys) + 1
    else:
        next_id = len(cards) + 1

    card_key = str(next_id)
    new_card = _make_card_dict(card_key, front, back)
    cards[card_key] = new_card
    deck['len'] = str(len(cards))

    # persist to DB if deck document exists
    sid = str(deck_id)
    doc = _decks_col.find_one({'id': sid})
    if doc:
        cdoc = {
            'front': new_card['front'],
            'back': new_card['back'],
            'tags': new_card['tags'],
            'correct_count': new_card['correct_count'],
            'incorrect_count': new_card['incorrect_count'],
            'last_reviewed': new_card['last_reviewed'],
            'ease': new_card['ease'],
            'interval': new_card['interval'],
            'repetitions': new_card['repetitions'],
        }
        _decks_col.update_one({'id': sid}, {'$set': {f'cards.{card_key}': cdoc, 'len': str(len(cards))}})

    return new_card

def delete_card(deck_id, card_id):
    """Delete a card from a deck. Returns True if deleted, False otherwise."""
    deck = get_deck_by_id(deck_id)
    if not deck:
        return False

    card_key = str(card_id)

    sid = str(deck_id)
    doc = _decks_col.find_one({'id': sid})
    if doc:
        # remove card subdocument and update length
        _decks_col.update_one({'id': sid}, {'$unset': {f'cards.{card_key}': ''}})
        remaining = doc.get('cards', {}).copy()
        remaining.pop(card_key, None)
        _decks_col.update_one({'id': sid}, {'$set': {'len': str(len(remaining))}})
        return True

    cards = deck.get('cards', {})
    if card_key in cards:
        cards.pop(card_key, None)
        deck['len'] = str(len(cards))
        return True

    return False

def record_review(deck_id, card_id, correct: bool):
    """Record a review result for a card. Increment correct/incorrect_count and set last_reviewed.

    Returns the updated card dict, or None if not found.
    """
    deck = get_deck_by_id(deck_id)
    if not deck:
        return None

    # find matching key (keys may be int or str)
    found_key = None
    for k in deck.get('cards', {}).keys():
        if str(k) == str(card_id):
            found_key = str(k)
            break

    if found_key is None:
        return None

    card = deck['cards'].get(found_key)
    if not card:
        return None

    if correct:
        card['correct_count'] = int(card.get('correct_count', 0)) + 1
    else:
        card['incorrect_count'] = int(card.get('incorrect_count', 0)) + 1

    # update last reviewed timestamp
    card['last_reviewed'] = datetime.now().isoformat()

    # persist to DB if deck exists there
    sid = str(deck_id)
    doc = _decks_col.find_one({'id': sid})
    if doc:
        _decks_col.update_one({'id': sid}, {'$set': {
            f'cards.{found_key}.correct_count': card.get('correct_count', 0),
            f'cards.{found_key}.incorrect_count': card.get('incorrect_count', 0),
            f'cards.{found_key}.last_reviewed': card.get('last_reviewed')
        }})

    return card

def create_deck(name, summary):
    """Create a new deck with the given name and summary.

    Returns the new deck dict.
    """
    # determine next deck id
    existing_ids = []
    for deck in _db.decks.find({}):
        try:
            existing_ids.append(int(deck['id']))
        except Exception:
            pass
    if existing_ids:
        next_id = max(existing_ids) + 1
    else:
        next_id = 1

    deck_id = str(next_id)
    new_deck = _make_deck_dict(deck_id, name, summary, cards_map={})

    # persist to DB
    cdoc = {
        'id': deck_id,
        'name': name,
        'summary': summary,
        'len': '0',
        'cards': {},
    }
    _decks_col.insert_one(cdoc)

    return new_deck

def add_deck_to_user(username, deck_id):
    """Add a deck to the user's study data.

    Returns True on success, False on failure.
    """
    if not username or not deck_id:
        return False

    sid = str(deck_id)
    user_doc = _users_col.find_one({'username': username})
    if not user_doc:
        return False

    study_data = user_doc.get('studyData', {})
    decks = study_data.get('decks', [])
    if sid in decks:
        return True  # already present

    decks.append(sid)
    study_data['decks'] = decks

    _users_col.update_one({'username': username}, {'$set': {'studyData': study_data}})
    return True