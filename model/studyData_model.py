from .login_model import USERS, get_user_by_username
from datetime import datetime
"""
Login model with hardcoded user data for teaching purposes.
No database connection required.
"""
DecksJson = {
    "1": {
        'id': "1",
        'name': 'Spanish Basics',
        'summary': 'Spanish flashcard deck.',
        'len': '150',
        'cards': {
            1: ('Hola', 'Hello'),
            2: ('Adiós', 'Goodbye'),
            3: ('Gracias', 'Thank you'),
        },
    },
    "2": {
        'id': "2",
        'name': 'French Basics',
        'summary': 'French flashcard deck.',
        'len': '200',
        'cards': {
            1: ('Bonjour', 'Hello'),
            2: ('Au revoir', 'Goodbye'),
            3: ('Merci', 'Thank you'),
        },
    },
}

class Card():
    """
    Representation of a single flashcard in a deck.
    Designed to interoperate with the DECKS data structure where cards are stored
    as {index: (front, back)} tuples.

    Attributes:
        id (int): Numeric index of the card within a deck.
        front (str): Text on the front of the card (question/term).
        back (str): Text on the back of the card (answer/definition).
        tags (list): Optional list of tags/categories for the card.
        correct_count (int): Times answered correctly.
        incorrect_count (int): Times answered incorrectly.
        last_reviewed (datetime|None): Last review timestamp.
        ease (float): Ease factor used by a simple spaced-repetition algorithm.
        interval (int): Current interval in days until next review.
        repetitions (int): Consecutive correct repetitions.
    """
    def __init__(self, id:int, front:str, back:str, tags=None,
                 correct_count:int=0, incorrect_count:int=0,
                 last_reviewed:datetime=None, ease:float=2.5,
                 interval:int=0, repetitions:int=0):
        self.id = int(id)
        self.front = front
        self.back = back
        self.tags = list(tags) if tags else []
        self.correct_count = int(correct_count)
        self.incorrect_count = int(incorrect_count)
        self.last_reviewed = last_reviewed
        self.ease = float(ease)
        self.interval = int(interval)
        self.repetitions = int(repetitions)

    @classmethod
    def from_tuple(cls, id, tpl):
        """
        Create a Cards instance from a tuple like (front, back),
        which matches the DECKS card storage format.
        """
        front, back = tpl
        return cls(id=id, front=front, back=back)

    def to_tuple(self):
        """Return (front, back) tuple compatible with DECKS storage."""
        return (self.front, self.back)

    def __getitem__(self, index):
        """Allow tuple-like access: card[0] -> front, card[1] -> back.

        This keeps Jinja templates that index into card tuples working when
        cards are Card instances.
        """
        if index == 0:
            return self.front
        if index == 1:
            return self.back
        raise IndexError('Card index out of range')

    def to_dict(self):
        """Serialize card to a plain dict for JSON/storage."""
        return {
            "id": self.id,
            "front": self.front,
            "back": self.back,
            "tags": self.tags,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "last_reviewed": self.last_reviewed.isoformat() if self.last_reviewed else None,
            "ease": self.ease,
            "interval": self.interval,
            "repetitions": self.repetitions,
        }
    def lenBack(self):
        """Return Length of the back card"""
        return len(self.back)
    def lenFront(self):
        """Return Length of the back card"""
        return len(self.back)

    def review(self, correct:bool, reviewed_at:datetime=None):
        """
        Update review stats using a simple SM-2-like heuristic.
        correct: whether the user answered correctly.
        """
        now = reviewed_at or datetime.utcnow()
        self.last_reviewed = now

        if correct:
            self.correct_count += 1
            self.repetitions += 1
            # adjust ease slightly upward on success
            self.ease = max(1.3, self.ease + 0.1)
            if self.repetitions == 1:
                self.interval = 1
            elif self.repetitions == 2:
                self.interval = 6
            else:
                # multiply previous interval by ease and round
                self.interval = max(1, int(round(self.interval * self.ease)))
        else:
            self.incorrect_count += 1
            self.repetitions = 0
            # penalize ease on failure
            self.ease = max(1.3, self.ease - 0.2)
            self.interval = 1

        return {
            "id": self.id,
            "next_interval_days": self.interval,
            "ease": self.ease,
            "repetitions": self.repetitions,
            "last_reviewed": self.last_reviewed,
        }

class Deck():
    def __init__(self, id:str, name:str, summary:str, length:str, cards):
        self.id = id
        self.name = name
        self.summary = summary
        # keep both attribute names for compatibility with existing templates
        # which reference `deck.len` and the newer code using `deck.length`.
        self.length = length
        self.len = length
        self.cards = cards

    def to_dict(self):
        """Return a plain-dict representation of the deck (cards as tuples).

        Useful for templates or APIs expecting simple serializable structures.
        """
        return {
            'id': self.id,
            'name': self.name,
            'summary': self.summary,
            'len': self.len,
            'cards': {cid: card.to_tuple() for cid, card in self.cards.items()}
        }

def DeckImportJSON(json):
    decks = []
    for deck_id, deck_data in json.items():
        cardsFromJson = {}
        for card_id, card_tuple in deck_data['cards'].items():  
            cardsFromJson[card_id] = Card.from_tuple(card_id, card_tuple)
        deck = Deck(
            id=deck_data['id'],
            name=deck_data['name'],
            summary=deck_data['summary'],
            length=deck_data['len'],
            cards=cardsFromJson
        )
        decks.append(deck)
    return decks
DECKS = DeckImportJSON(DecksJson)


def get_deck_by_id(deck_id):
    """
    Retrieve a deck by its ID from the hardcoded decks.
    
    Args:
        deck_id (int): The ID of the deck to retrieve"""
    # DECKS is a list of Deck instances. Match by id (string or int accepted).
    if deck_id is None:
        return None
    for deck in DECKS:
        try:
            if str(deck.id) == str(deck_id):
                return deck
        except AttributeError:
            # in case an unexpected structure is present, skip
            continue
    return None

def get_user_study_data(username):
    """
    Retrieve study data for a given user.
    
    Args:
        username (str): The username of the user"""
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
    user = get_user_by_username(username)
    if not user or 'studyData' not in user:
        return []

    deck_ids = user['studyData'].get('decks', [])
    decks = []
    for deck_id in deck_ids:
        deck = get_deck_by_id(deck_id)
        if deck:
            # return the Deck instance directly; callers can access deck.cards
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

    if key in deck.cards:
        card = deck.cards[key]
        card.front = front
        card.back = back
        return True

    # if card not present, create it
    try:
        new_card = Card.from_tuple(key, (front, back))
    except Exception:
        new_card = Card(id=key, front=front, back=back)
    deck.cards[key] = new_card
    deck.len = str(len(deck.cards))
    deck.length = deck.len
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

    new_card = Card(id=next_id, front=front, back=back)
    deck.cards[next_id] = new_card
    deck.len = str(len(deck.cards))
    deck.length = deck.len
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
        return True

    return False
