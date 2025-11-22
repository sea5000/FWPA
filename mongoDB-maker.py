from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient("mongodb://localhost:27017")

db = client["mydatabase"]
users = db["users"]
decks = db["decks"]
cards = db["cards"]

# helper to produce ISO timestamps
def iso_days_ago(days: int):
    return (datetime.utcnow() - timedelta(days=days)).isoformat()

# Deck documents with full card metadata to match model expectations
DecksJson = [
    {
        'id': "1",
        'name': 'Spanish Basics',
        'summary': 'Spanish flashcard deck.',
        'len': '3',
        'cards': {
            '1': {
                'front': 'Hola',
                'back': 'Hello',
                'tags': ['greeting', 'basic'],
                'correct_count': 5,
                'incorrect_count': 1,
                'last_reviewed': iso_days_ago(1),
                'ease': 2.8,
                'interval': 3,
                'repetitions': 2,
            },
            '2': {
                'front': 'Adiós',
                'back': 'Goodbye',
                'tags': ['farewell', 'basic'],
                'correct_count': 3,
                'incorrect_count': 2,
                'last_reviewed': iso_days_ago(4),
                'ease': 2.3,
                'interval': 1,
                'repetitions': 1,
            },
            '3': {
                'front': 'Gracias',
                'back': 'Thank you',
                'tags': ['politeness', 'basic'],
                'correct_count': 10,
                'incorrect_count': 0,
                'last_reviewed': iso_days_ago(10),
                'ease': 3.2,
                'interval': 15,
                'repetitions': 5,
            },
        },
    },
    {
        'id': "2",
        'name': 'French Basics',
        'summary': 'French flashcard deck.',
        'len': '3',
        'cards': {
            '1': {
                'front': 'Bonjour',
                'back': 'Hello',
                'tags': ['greeting', 'basic'],
                'correct_count': 7,
                'incorrect_count': 1,
                'last_reviewed': iso_days_ago(2),
                'ease': 2.9,
                'interval': 5,
                'repetitions': 3,
            },
            '2': {
                'front': 'Au revoir',
                'back': 'Goodbye',
                'tags': ['farewell', 'basic'],
                'correct_count': 2,
                'incorrect_count': 3,
                'last_reviewed': iso_days_ago(7),
                'ease': 2.1,
                'interval': 0,
                'repetitions': 0,
            },
            '3': {
                'front': 'Merci',
                'back': 'Thank you',
                'tags': ['politeness', 'basic'],
                'correct_count': 12,
                'incorrect_count': 0,
                'last_reviewed': iso_days_ago(30),
                'ease': 3.5,
                'interval': 30,
                'repetitions': 8,
            },
        },
    },
]

USERS = [
    {
        'id': 1,
        'username': 'admin',
        'password': 'admin123',
        'name': 'Admin User',
        'email': 'admin@example.com',
        'profile_pic': None,
        'studyData': {'streak': 50000, 'lastLogin': iso_days_ago(0), 'decks': ["1", "2"], 'loginHistory': {iso_days_ago(1): 1, iso_days_ago(2): 1}}
    },
    {
        'id': 2,
        'username': 'student',
        'password': 'student123',
        'name': 'Student User',
        'email': 'student@example.com',
        'profile_pic': 'https://ui-avatars.com/api/?name=Student+User&background=0D6EFD&color=fff&size=200',
        'studyData': {'streak': 2, 'lastLogin': iso_days_ago(3), 'decks': ["2"], 'loginHistory': {iso_days_ago(3): 1, iso_days_ago(4): 1}}
    },
    {
        'id': 3,
        'username': 'teacher',
        'password': 'teacher123',
        'name': 'Teacher User',
        'email': 'teacher@example.com',
        'profile_pic': None,
        'studyData': {'streak': 400, 'lastLogin': iso_days_ago(10), 'decks': ["1"], 'loginHistory': {iso_days_ago(10): 1, iso_days_ago(11): 1}}
    }
]


def seed():
    # clear existing data
    users.delete_many({})
    decks.delete_many({})
    cards.delete_many({})

    # insert users and decks
    users.insert_many(USERS)
    decks.insert_many(DecksJson)
    # keep a copy in the legacy 'cards' collection for compatibility
    cards.insert_many(DecksJson)


if __name__ == '__main__':
    seed()
    print("Database and collections created, sample data inserted into 'users', 'decks', and 'cards'.")
from pymongo import MongoClient

# client = MongoClient("mongodb://localhost:27017")

# db = client["mydatabase"]
# users = db["users"]
# cards = db["cards"]

# DecksJson = [{
#         'id': "1",
#         'name': 'Spanish Basics',
#         'summary': 'Spanish flashcard deck.',
#         'len': '150',
#         'cards': {
#             '1': {'front':'Hola', 'back':'Hello'},
#             '2': ('Adiós', 'Goodbye'),
#             '3': ('Gracias', 'Thank you'),
#         },
#     },{
#         'id': "2",
#         'name': 'French Basics',
#         'summary': 'French flashcard deck.',
#         'len': '200',
#         'cards': {
#             '1': ('Bonjour', 'Hello'),
#             '2': ('Au revoir', 'Goodbye'),
#             '3': ('Merci', 'Thank you'),
#         },
#     },
# ]

# USERS = [{
#         'id': 1,
#         'username': 'admin',
#         'password': 'admin123',
#         'name': 'Admin',
#         'email': 'admin@example.com',
#         'studyData': {'streak': 50000, 'lastLogin': '2024-06-01', 'decks': ["1","2"], 'loginHistory': {'2025-11-21': 67, '2025-11-22': 45}}
#     },
#     {
#         'id': 2,
#         'username': 'student',
#         'password': 'student123',
#         'name': 'Student',
#         'email': 'student@example.com',
#         'studyData': {'streak': 2, 'lastLogin': '2024-06-01', 'decks': ["2"], 'loginHistory': {'2025-11-21': 67, '2025-11-22': 45}}
#     },
#     {
#         'id': 3,
#         'username': 'teacher',
#         'password': 'teacher123',
#         'name': 'Teacher',
#         'email': 'teacher@example.com',
#         'studyData': {'streak': 400, 'lastLogin': '2024-06-01', 'decks': ["1"], 'loginHistory': {'2025-11-21': 67, '2025-11-22': 45} }
#     }
# ]

# # Insert a document
# #users.insert_one({"name": "Alice", "age": 30})
# users.delete_many({})
# cards.delete_many({})
# users.insert_many(USERS)
# cards.insert_many(DecksJson)
# print("Database and collections created, sample data inserted.")