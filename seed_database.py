#!/usr/bin/env python3
"""Seed MongoDB for the new 12-collection schema.

Collections populated:
- profiles
- authentication
- relationships
- user_permissions
- decks
- cards
- ai_generation_logs
- deck_tags
- posts
- notes
- interactions
- study_sessions
"""

import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from utils.auth import get_pepper_by_version, combine_password_and_pepper, ph, get_current_pepper_version

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("MONGO_DB", "bookme")
client = MongoClient(MONGO_URI)
db = client[DB_NAME]


def iso_days_ago(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).isoformat()


def gen_hashed_password(password: str) -> str:
    version = get_current_pepper_version()
    if not version:
        raise RuntimeError("Current pepper version missing; set in environment.")
    pepper = get_pepper_by_version(version)
    combined = combine_password_and_pepper(password, pepper)
    return ph.hash(combined)


def clear_collections() -> None:
    collections = [
        "profiles",
        "authentication",
        "relationships",
        "user_permissions",
        "decks",
        "cards",
        "ai_generation_logs",
        "deck_tags",
        "posts",
        "notes",
        "interactions",
        "study_sessions",
        # legacy names to keep the database clean during migration
        "users",
        "sessions",
    ]
    for name in collections:
        db[name].delete_many({})
    print("✓ Cleared collections")


def seed_profiles_and_auth():
    password_hash = gen_hashed_password("password123")
    version = get_current_pepper_version()
    profiles = [
        {
            "id": "1",
            "username": "alice",
            "name": "Alice Chen",
            "email": "alice@example.com",
            "profile_pic": "https://i.pravatar.cc/150?img=5",
            "bio": "Computer Science major | ML enthusiast | Coffee addict",
            "studyData": {"streak": 15, "lastLogin": iso_days_ago(0)},
            "interests": ["machine learning", "python", "productivity"],
            "recentSearches": ["transformers", "anki ease factor", "linux shortcuts"],
        },
        {
            "id": "2",
            "username": "james",
            "name": "James Miller",
            "email": "james@example.com",
            "profile_pic": "https://i.pravatar.cc/150?img=12",
            "bio": "Biology student | Nature lover",
            "studyData": {"streak": 8, "lastLogin": iso_days_ago(1)},
            "interests": ["biology", "health", "outdoors"],
            "recentSearches": ["cell division", "flashcard tips"],
        },
        {
            "id": "3",
            "username": "sophia",
            "name": "Sophia Nguyen",
            "email": "sophia@example.com",
            "profile_pic": "https://i.pravatar.cc/150?img=16",
            "bio": "Math & Physics | Chess player",
            "studyData": {"streak": 23, "lastLogin": iso_days_ago(0)},
            "interests": ["physics", "math", "chess"],
            "recentSearches": ["eigenvalues", "spaced repetition"],
        },
        {
            "id": "4",
            "username": "emma",
            "name": "Emma Wilson",
            "email": "emma@example.com",
            "profile_pic": "https://i.pravatar.cc/150?img=10",
            "bio": "Chemistry nerd | Lab enthusiast",
            "studyData": {"streak": 19, "lastLogin": iso_days_ago(0)},
            "interests": ["chemistry", "labs", "data viz"],
            "recentSearches": ["organic mechanisms", "lab safety"],
        },
        {
            "id": "5",
            "username": "admin",
            "name": "Admin User",
            "email": "admin@example.com",
            "profile_pic": None,
            "bio": "Admin account",
            "studyData": {"streak": 1, "lastLogin": iso_days_ago(0)},
            "interests": ["ops", "security"],
            "recentSearches": [],
        },
    ]
    auth = [
        {
            "username": p["username"],
            "password_hash": password_hash,
            "pepper_version": version,
            "created_at": datetime.utcnow().isoformat(),
        }
        for p in profiles
    ]
    db.profiles.insert_many(profiles)
    db.authentication.insert_many(auth)
    print(f"✓ Seeded {len(profiles)} profiles and authentication records")


def seed_relationships():
    rels = [
        {"follower": "alice", "following": "james", "created_at": iso_days_ago(2)},
        {"follower": "sophia", "following": "alice", "created_at": iso_days_ago(1)},
        {"follower": "emma", "following": "alice", "created_at": iso_days_ago(1)},
        {"follower": "james", "following": "emma", "created_at": iso_days_ago(4)},
    ]
    if rels:
        db.relationships.insert_many(rels)
    print(f"✓ Seeded {len(rels)} relationships")


def seed_decks_cards_tags_permissions():
    decks = [
        {
            "id": "1",
            "name": "Spanish Basics",
            "summary": "Greetings and essentials",
            "subject": "Spanish",
            "category": "Languages",
            "tags": ["greeting", "basic"],
            "cards": [
                {"id": "1", "front": "Hola", "back": "Hello", "tags": ["greeting"]},
                {"id": "2", "front": "Adiós", "back": "Goodbye", "tags": ["farewell"]},
                {"id": "3", "front": "Gracias", "back": "Thank you", "tags": ["politeness"]},
            ]
        },
        {
            "id": "2",
            "name": "French Basics",
            "summary": "Common phrases",
            "subject": "French",
            "category": "Languages",
            "tags": ["greeting", "basic"],
            "cards": [
                {"id": "1", "front": "Bonjour", "back": "Hello", "tags": ["greeting"]},
                {"id": "2", "front": "Au revoir", "back": "Goodbye", "tags": ["farewell"]},
                {"id": "3", "front": "Merci", "back": "Thank you", "tags": ["politeness"]},
            ]
        },
    ]

    deck_docs = []
    card_docs = []
    tag_docs = []
    perm_docs = [{'deck_id': '1', 'reviewers': ['admin', 'all'], 'editors': ['admin', 'alice'], 'owner': 'alice'},
                 {'deck_id': '2', 'reviewers': ['admin', 'all'], 'editors': ['admin', 'james'], 'owner': 'james'}]

    for deck in decks:
        deck_docs.append({
            "id": deck["id"],
            "name": deck["name"],
            "summary": deck["summary"],
            "subject": deck.get("subject"),
            "category": deck.get("category"),
            "len": str(len(deck.get("cards", []))),
        })
        tag_docs.extend({"deck_id": deck["id"], "tag": t} for t in deck.get("tags", []))
        for card in deck.get("cards", []):
            card_docs.append({
                "deck_id": deck["id"],
                "id": str(card["id"]),
                "front": card["front"],
                "back": card["back"],
                "tags": card.get("tags", []),
                "correct_count": 0,
                "incorrect_count": 0,
                "last_reviewed": None,
                "ease": 2.5,
                "interval": 0,
                "repetitions": 0,
            })
        for owner in deck.get("owners", []):
            perm_docs.append({"username": owner, "deck_id": deck["id"], "role": "owner"})

    if deck_docs:
        db.decks.insert_many(deck_docs)
    if tag_docs:
        db.deck_tags.insert_many(tag_docs)
    if card_docs:
        db.cards.insert_many(card_docs)
    if perm_docs:
        db.user_permissions.insert_many(perm_docs)

    ai_logs = [
        {
            "deck_id": "1",
            "prompt": "Generate 5 beginner Spanish greeting flashcards",
            "result": "Hola/Hello, Adiós/Goodbye, Gracias/Thank you",
            "created_by": "alice",
            "created_at": datetime.utcnow().isoformat(),
        }
    ]
    db.ai_generation_logs.insert_many(ai_logs)
    print(f"✓ Seeded {len(deck_docs)} decks, {len(card_docs)} cards, {len(tag_docs)} tags, {len(perm_docs)} permissions")


def seed_posts_and_interactions():
    posts = [
        {"author": "alice", "text": "Studying ML — gradient descent visualized", "image": None, "timestamp": iso_days_ago(0)},
        {"author": "james", "text": "Photosynthesis summary is up!", "image": None, "timestamp": iso_days_ago(1)},
        {"author": "sophia", "text": "Group study on calculus was great", "image": None, "timestamp": iso_days_ago(2)},
    ]
    result = db.posts.insert_many(posts)
    interactions = [
        {
            "entity_type": "post",
            "entity_id": str(result.inserted_ids[0]),
            "likes": ["james", "sophia"],
            "comments": [
                {"author": "james", "text": "Great visual!", "timestamp": iso_days_ago(0)},
            ],
        },
        {
            "entity_type": "post",
            "entity_id": str(result.inserted_ids[1]),
            "likes": ["alice"],
            "comments": [],
        },
        {
            "entity_type": "post",
            "entity_id": str(result.inserted_ids[2]),
            "likes": ["emma"],
            "comments": [
                {"author": "emma", "text": "Count me in next time!", "timestamp": iso_days_ago(1)},
            ],
        },
    ]
    db.interactions.insert_many(interactions)
    print(f"✓ Seeded {len(posts)} posts with interactions")


def seed_notes_and_interactions():
    notes = [
        {
            "title": "Calculus Derivatives Cheat Sheet",
            "subject": "Mathematics",
            "content": "Key derivative rules and examples",
            "author": "sophia",
            "views": 12,
            "tags": ["calculus", "derivatives"],
            "timestamp": datetime.utcnow(),
        },
        {
            "title": "Cell Biology - Mitosis vs Meiosis",
            "subject": "Biology",
            "content": "Side-by-side comparison of cell division",
            "author": "james",
            "views": 18,
            "tags": ["cell-biology", "mitosis"],
            "timestamp": datetime.utcnow(),
        },
        {
            "title": "Python Basics - Data Structures",
            "subject": "Programming",
            "content": "Lists, tuples, dicts, and sets in Python",
            "author": "alice",
            "views": 20,
            "tags": ["python", "data-structures"],
            "timestamp": datetime.utcnow(),
        },
    ]
    result = db.notes.insert_many(notes)
    interactions = [
        {
            "entity_type": "note",
            "entity_id": str(result.inserted_ids[0]),
            "likes": ["alice", "emma"],
            "comments": [
                {"author": "alice", "text": "Super helpful", "timestamp": iso_days_ago(0)},
            ],
        },
        {
            "entity_type": "note",
            "entity_id": str(result.inserted_ids[1]),
            "likes": ["sophia"],
            "comments": [],
        },
        {
            "entity_type": "note",
            "entity_id": str(result.inserted_ids[2]),
            "likes": ["sophia", "james"],
            "comments": [
                {"author": "james", "text": "Great primer!", "timestamp": iso_days_ago(1)},
            ],
        },
    ]
    db.interactions.insert_many(interactions)
    print(f"✓ Seeded {len(notes)} notes with interactions")


def seed_study_sessions():
    now = datetime.utcnow()
    sessions = []
    for user in ["alice", "james", "sophia", "emma"]:
        for i in range(3):
            sessions.append({
                "user": user,
                "duration": 25 * 60,
                "subject": "Math" if user in ("alice", "sophia") else "Biology",
                "mode": "Pomodoro",
                "timestamp": now - timedelta(days=i),
            })
    db.study_sessions.insert_many(sessions)
    print(f"✓ Seeded {len(sessions)} study sessions")


def print_summary():
    counts = {
        "Profiles": db.profiles.count_documents({}),
        "Authentication": db.authentication.count_documents({}),
        "Relationships": db.relationships.count_documents({}),
        "UserPermissions": db.user_permissions.count_documents({}),
        "Decks": db.decks.count_documents({}),
        "Cards": db.cards.count_documents({}),
        "DeckTags": db.deck_tags.count_documents({}),
        "AIGenerationLogs": db.ai_generation_logs.count_documents({}),
        "Posts": db.posts.count_documents({}),
        "Notes": db.notes.count_documents({}),
        "Interactions": db.interactions.count_documents({}),
        "StudySessions": db.study_sessions.count_documents({}),
    }
    print("\nSeed summary:")
    for name, count in counts.items():
        print(f"  {name}: {count}")


def main():
    clear_collections()
    seed_profiles_and_auth()
    seed_relationships()
    seed_decks_cards_tags_permissions()
    seed_posts_and_interactions()
    seed_notes_and_interactions()
    seed_study_sessions()
    print_summary()


if __name__ == "__main__":
    main()
