from .login_model import get_user_by_username
from datetime import datetime
from .mongo import get_db
from typing import Optional

# MongoDB setup (configurable via MONGO_URI env)
_db = get_db()
_profiles_col = _db.profiles
_decks_col = _db.decks
_cards_col = _db.cards
_permissions_col = _db.user_permissions
_deck_tags_col = _db.deck_tags
_ai_logs_col = _db.ai_generation_logs


def _refresh_deck_length(deck_id: str) -> None:
    """Keep the deck length in sync with the cards collection."""
    count = _cards_col.count_documents({'deck_id': deck_id})
    _decks_col.update_one({'id': deck_id}, {'$set': {'len': str(count)}})

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

def _make_deck_dict(did, name, summary, cards_map, subject=None, category=None, tags=None):
    """Create a plain dict representing a deck; cards_map values should be card dicts."""
    return {
        'id': str(did),
        'name': name,
        'summary': summary,
        'subject': subject,
        'category': category,
        'tags': tags or [],
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
        cards = {}
        for cdoc in _cards_col.find({'deck_id': sid}).sort('id', 1):
            cid = cdoc.get('id') or cdoc.get('_id')
            try:
                last = cdoc.get('last_reviewed')
                last_dt = datetime.fromisoformat(last) if last else None
            except Exception:
                last_dt = None
            cards[str(cid)] = _make_card_dict(
                cid,
                cdoc.get('front'),
                cdoc.get('back'),
                tags=cdoc.get('tags', []),
                correct_count=cdoc.get('correct_count', 0),
                incorrect_count=cdoc.get('incorrect_count', 0),
                last_reviewed=last_dt,
                ease=cdoc.get('ease', 2.5),
                interval=cdoc.get('interval', 0),
                repetitions=cdoc.get('repetitions', 0),
            )

        tags_doc = list(_deck_tags_col.find({'deck_id': sid}))
        tag_values = [t.get('tag') for t in tags_doc if t.get('tag')]
        deck = _make_deck_dict(
            doc.get('id'),
            doc.get('name'),
            doc.get('summary', ''),
            cards,
            subject=doc.get('subject'),
            category=doc.get('category'),
            tags=tag_values,
        )
        return deck

def get_user_study_data(username):
    """
    Retrieve study data for a given user.
    
    Args:
        username (str): The username of the user"""
    # prefer DB-backed users
    if not username:
        return None
    doc = _profiles_col.find_one({'username': username}) or get_user_by_username(username)
    study_data = None
    if doc and 'studyData' in doc:
        study_data = doc.get('studyData') or {}

    # derive deck ids from user_permissions to keep templates working
    if study_data is None:
        study_data = {}
    permitted = list(_permissions_col.find({'username': username}))
    study_data['decks'] = [p.get('deck_id') for p in permitted if p.get('deck_id')]
    return study_data

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
    if not username:
        return []
    
    # Code to give admin access to all decks, should probably be removed for production.
    if username == "admin":
        # admin gets all decks
        deck_ids = [d.get('id') for d in _decks_col.find({}) if d.get('id')]
        decks = []
        for deck_id in deck_ids:
            deck = get_deck_by_id(deck_id)
            if deck:
                decks.append(deck)
        return decks
    ### END admin special case ###
    deck_ids = [p.get('deck_id') for p in _permissions_col.find({'username': username}) if p.get('deck_id')]
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

def update_deckInfo(deck_id, name: Optional[str] = None, summary: Optional[str] = None, subject: Optional[str] = None, category: Optional[str] = None, tags: Optional[list] = None):
    """Update deck metadata fields."""
    deck = get_deck_by_id(deck_id)
    if not deck:
        return False

    sid = str(deck_id)
    update_doc = {}
    if name is not None:
        deck['name'] = name
        update_doc['name'] = name
    if summary is not None:
        deck['summary'] = summary
        update_doc['summary'] = summary
    if subject is not None:
        update_doc['subject'] = subject
    if category is not None:
        update_doc['category'] = category

    if update_doc:
        _decks_col.update_one({'id': sid}, {'$set': update_doc})

    if tags is not None:
        _deck_tags_col.delete_many({'deck_id': sid})
        if tags:
            _deck_tags_col.insert_many([{'deck_id': sid, 'tag': t} for t in tags])
    return True

def update_card(deck_id, card_id, front, back):
    """Update an existing card's front/back in the in-memory deck.

    Returns True if updated, False if deck not found.
    """
    deck = get_deck_by_id(deck_id)
    if not deck:
        return False
    # normalize key to string for storage keys
    card_key = str(card_id)

    sid = str(deck_id)
    update_doc = {
        'front': front,
        'back': back,
    }
    res = _cards_col.update_one({'deck_id': sid, 'id': card_key}, {'$set': update_doc})
    if res.matched_count == 0:
        # create if missing to keep API lenient
        new_card = _make_card_dict(card_key, front, back)
        new_card['deck_id'] = sid
        _cards_col.insert_one(new_card)
    _refresh_deck_length(sid)
    return True

def add_card(deck_id, front, back):
    """Add a new card to the deck and return the new Card instance.

    The new card id tries to follow numeric indexing when existing keys are numeric.
    """
    deck = get_deck_by_id(deck_id)
    if not deck:
        return None

    sid = str(deck_id)
    existing_cards = list(_cards_col.find({'deck_id': sid}))

    numeric_keys = []
    for c in existing_cards:
        cid = c.get('id')
        if isinstance(cid, int) or (isinstance(cid, str) and str(cid).isdigit()):
            numeric_keys.append(int(cid))

    if numeric_keys:
        next_id = max(numeric_keys) + 1
    else:
        next_id = len(existing_cards) + 1

    card_key = str(next_id)
    new_card = _make_card_dict(card_key, front, back)
    new_card['deck_id'] = sid

    _cards_col.insert_one(new_card)
    _refresh_deck_length(sid)
    return new_card

def delete_card(deck_id, card_id):
    """Delete a card from a deck. Returns True if deleted, False otherwise."""
    deck = get_deck_by_id(deck_id)
    if not deck:
        return False

    card_key = str(card_id)
    sid = str(deck_id)
    res = _cards_col.delete_one({'deck_id': sid, 'id': card_key})
    if res.deleted_count > 0:
        _refresh_deck_length(sid)
        return True
    return False

def delete_deck(deck_id):
    """Delete a deck by its ID. Returns True if deleted, False otherwise."""
    sid = str(deck_id)
    _cards_col.delete_many({'deck_id': sid})
    _deck_tags_col.delete_many({'deck_id': sid})
    _permissions_col.delete_many({'deck_id': sid})
    result = _decks_col.delete_one({'id': sid})
    return result.deleted_count > 0

def record_review(deck_id, card_id, correct: bool):
    """Record a review result for a card. Increment correct/incorrect_count and set last_reviewed.

    Returns the updated card dict, or None if not found.
    """
    deck = get_deck_by_id(deck_id)
    if not deck:
        return None

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

    card['last_reviewed'] = datetime.now().isoformat()

    sid = str(deck_id)
    _cards_col.update_one(
        {'deck_id': sid, 'id': found_key},
        {'$set': {
            'correct_count': card.get('correct_count', 0),
            'incorrect_count': card.get('incorrect_count', 0),
            'last_reviewed': card.get('last_reviewed'),
        }},
    )

    return card

def create_deck(name, summary, subject: Optional[str] = None, category: Optional[str] = None, tags: Optional[list] = None):
    """Create a new deck with the given name and summary."""
    existing_ids = []
    for deck in _decks_col.find({}):
        try:
            existing_ids.append(int(deck['id']))
        except Exception:
            pass
    if existing_ids:
        next_id = max(existing_ids) + 1
    else:
        next_id = 1

    deck_id = str(next_id)
    new_deck = _make_deck_dict(deck_id, name, summary, cards_map={}, subject=subject, category=category, tags=tags)

    cdoc = {
        'id': deck_id,
        'name': name,
        'summary': summary,
        'subject': subject,
        'category': category,
        'len': '0',
    }
    _decks_col.insert_one(cdoc)
    if tags:
        _deck_tags_col.insert_many([{'deck_id': deck_id, 'tag': t} for t in tags])

    return new_deck

def add_deck_to_user(username, deck_id):
    """Add a deck to the user's study data.

    Returns True on success, False on failure.
    """
    if not username or not deck_id:
        return False

    sid = str(deck_id)
    user_doc = _profiles_col.find_one({'username': username})
    if not user_doc:
        return False

    existing = _permissions_col.find_one({'username': username, 'deck_id': sid})
    if existing:
        return True

    _permissions_col.insert_one({'username': username, 'deck_id': sid, 'role': 'owner'})
    return True