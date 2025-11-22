from .login_model import get_user_by_username
from datetime import datetime
from pymongo import MongoClient
import os
from typing import Optional, Dict

# MongoDB setup (configurable via MONGO_URI env)
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
_client = MongoClient(MONGO_URI)
_db = _client.get_database('mydatabase')
_users_col = _db.get_collection('users')
_decks_col = _db.get_collection('decks')
"""
Login model with hardcoded user data for teaching purposes.
No database connection required.
"""
client = MongoClient("mongodb://localhost:27017")

db = client["mydatabase"]
cards = db["cards"]

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

def DeckImportJSON(json):
    decks = []
    for deck_id, deck_data in json.items():
        cardsFromJson = {}
        for card_id, card_tuple in deck_data['cards'].items():
            front, back = card_tuple
            cardsFromJson[card_id] = _make_card_dict(card_id, front, back)
        deck = _make_deck_dict(deck_data['id'], deck_data['name'], deck_data.get('summary',''), cardsFromJson)
        decks.append(deck)
    return decks
DECKS = DeckImportJSON({})


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
            cards[int(cid) if str(cid).isdigit() else cid] = _make_card_dict(cid, cdoc.get('front'), cdoc.get('back'), tags=cdoc.get('tags', []), correct_count=cdoc.get('correct_count', 0), incorrect_count=cdoc.get('incorrect_count', 0), last_reviewed=last_dt, ease=cdoc.get('ease',2.5), interval=cdoc.get('interval',0), repetitions=cdoc.get('repetitions',0))
        deck = _make_deck_dict(doc.get('id'), doc.get('name'), doc.get('summary',''), cards)
        return deck

    # fallback to in-memory DECKS list
    for deck in DECKS:
        try:
            if str(deck.id) == sid:
                return deck
        except AttributeError:
            continue
    return None

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
    # normalize key to int when possible
    try:
        key = int(card_id)
    except Exception:
        key = card_id

    # try to persist to MongoDB if deck exists there
    sid = str(deck_id)
    doc = _decks_col.find_one({'id': sid})
    if doc:
        # update card subdocument
        card_key = str(card_id)
        update_doc = {
            f'cards.{card_key}.front': front,
            f'cards.{card_key}.back': back,
        }
        _decks_col.update_one({'id': sid}, {'$set': update_doc})
        # also update in-memory Deck instance
        if key in deck.cards:
            deck.cards[key].front = front
            deck.cards[key].back = back
        return True

    if key in deck.cards:
        card = deck.cards[key]
        card.front = front
        card.back = back
        return True

    # if card not present, create it
    # create a card dict
    new_card = _make_card_dict(key, front, back)
    deck.cards[key] = new_card
    deck.len = str(len(deck.cards))
    deck.length = deck.len

    # persist to DB if deck document exists
    sid = str(deck_id)
    doc = _decks_col.find_one({'id': sid})
    if doc:
        # prepare card doc
        cdoc = {
            'front': new_card.front,
            'back': new_card.back,
            'tags': new_card.tags,
            'correct_count': new_card.correct_count,
            'incorrect_count': new_card.incorrect_count,
            'last_reviewed': new_card.last_reviewed.isoformat() if new_card.last_reviewed else None,
            'ease': new_card.ease,
            'interval': new_card.interval,
            'repetitions': new_card.repetitions,
        }
        _decks_col.update_one({'id': sid}, {'$set': {f'cards.{str(key)}': cdoc, 'len': str(len(deck.cards))}})
    return True


def add_card(deck_id, front, back):
    """Add a new card to the deck and return the new Card instance.

    The new card id tries to follow numeric indexing when existing keys are numeric.
    """
    deck = get_deck_by_id(deck_id)
    if not deck:
        return None

    # determine next id
    keys = list(deck.cards.keys())
    next_id = None
    numeric_keys = []
    for k in keys:
        try:
            numeric_keys.append(int(k))
        except Exception:
            pass
    if numeric_keys:
        next_id = max(numeric_keys) + 1
    else:
        # fallback to length+1 as string
        next_id = str(len(keys) + 1)

    new_card = _make_card_dict(next_id, front, back)
    deck.cards[next_id] = new_card
    deck.len = str(len(deck.cards))
    deck.length = deck.len

    # persist to DB if deck document exists
    sid = str(deck_id)
    doc = _decks_col.find_one({'id': sid})
    if doc:
        cdoc = {
            'front': new_card.front,
            'back': new_card.back,
            'tags': new_card.tags,
            'correct_count': new_card.correct_count,
            'incorrect_count': new_card.incorrect_count,
            'last_reviewed': new_card.last_reviewed.isoformat() if new_card.last_reviewed else None,
            'ease': new_card.ease,
            'interval': new_card.interval,
            'repetitions': new_card.repetitions,
        }
        _decks_col.update_one({'id': sid}, {'$set': {f'cards.{str(next_id)}': cdoc, 'len': str(len(deck.cards))}})

    return new_card


def delete_card(deck_id, card_id):
    """Delete a card from a deck. Returns True if deleted, False otherwise."""
    deck = get_deck_by_id(deck_id)
    if not deck:
        return False
    try:
        key = int(card_id)
    except Exception:
        key = card_id

    if key in deck.cards:
        try:
            del deck.cards[key]
        except KeyError:
            return False
        # update length fields
        deck.len = str(len(deck.cards))
        deck.length = deck.len

        # persist deletion to DB if present
        sid = str(deck_id)
        doc = _decks_col.find_one({'id': sid})
        if doc:
            _decks_col.update_one({'id': sid}, {'$unset': {f'cards.{str(key)}': 1}, '$set': {'len': str(len(deck.cards))}})

        return True

    return False
