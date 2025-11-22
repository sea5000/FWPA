from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client["mydatabase"]
users = db["users"]
cards = db["cards"]

DecksJson = [{
    "1": {
        'id': "1",
        'name': 'Spanish Basics',
        'summary': 'Spanish flashcard deck.',
        'len': '150',
        'cards': {
            '1': ('Hola', 'Hello'),
            '2': ('Adiós', 'Goodbye'),
            '3': ('Gracias', 'Thank you'),
        },
    },
    "2": {
        'id': "2",
        'name': 'French Basics',
        'summary': 'French flashcard deck.',
        'len': '200',
        'cards': {
            '1': ('Bonjour', 'Hello'),
            '2': ('Au revoir', 'Goodbye'),
            '3': ('Merci', 'Thank you'),
        },
    },
}]

USERS = [{
        'id': 1,
        'username': 'admin',
        'password': 'admin123',
        'name': 'Admin',
        'email': 'admin@example.com',
        'studyData': {'streak': 50000, 'lastLogin': '2024-06-01', 'decks': ["1","2"] }
    },
    {
        'id': 2,
        'username': 'student',
        'password': 'student123',
        'name': 'Student',
        'email': 'student@example.com',
        'studyData': {'streak': 2, 'lastLogin': '2024-06-01', 'decks': ["2"] }
    },
    {
        'id': 3,
        'username': 'teacher',
        'password': 'teacher123',
        'name': 'Teacher',
        'email': 'teacher@example.com',
        'studyData': {'streak': 400, 'lastLogin': '2024-06-01', 'decks': ["1"] }
    }
]

# Insert a document
#users.insert_one({"name": "Alice", "age": 30})
users.delete_many({})
cards.delete_many({})
users.insert_many(USERS)
cards.insert_many(DecksJson)
print("Database and collections created, sample data inserted.")