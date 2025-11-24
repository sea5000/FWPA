import os
from datetime import datetime, timedelta
from pymongo import MongoClient

# Use same defaults as model.mongo and login_model
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
bookme_db = MongoClient(MONGO_URI)['bookme']
users_db = MongoClient(MONGO_URI)['mydatabase']
users_col = users_db['users']


def seed_users():
    existing = list(users_col.find({}, {'_id': 0, 'username': 1}))
    existing_usernames = {u.get('username') for u in existing}
    demo = [
        {
            'id': '1', 'username': 'alice', 'password': 'password', 'name': 'Alice Chen',
            'email': 'alice@example.com', 'studyData': {'streak': 3, 'lastLogin': datetime.utcnow().isoformat(), 'decks': []}
        },
        {
            'id': '2', 'username': 'james', 'password': 'password', 'name': 'James Miller',
            'email': 'james@example.com', 'studyData': {'streak': 5, 'lastLogin': datetime.utcnow().isoformat(), 'decks': []}
        },
        {
            'id': '3', 'username': 'sophia', 'password': 'password', 'name': 'Sophia Nguyen',
            'email': 'sophia@example.com', 'studyData': {'streak': 1, 'lastLogin': datetime.utcnow().isoformat(), 'decks': []}
        },
    ]
    to_insert = [d for d in demo if d['username'] not in existing_usernames]
    if to_insert:
        users_col.insert_many(to_insert)
        print(f"Inserted {len(to_insert)} demo users")
    else:
        print("Users already seeded")


def seed_notes():
    if bookme_db.notes.count_documents({}) == 0:
        notes = [
            {
                'title': 'Derivatives Rules', 'content': 'Quick summary of differentiation formulas for test prep.',
                'author': 'alice', 'views': 0, 'timestamp': datetime.utcnow()
            },
            {
                'title': 'Cell Division Overview', 'content': 'Mitosis and meiosis steps with diagrams.',
                'author': 'james', 'views': 0, 'timestamp': datetime.utcnow()
            },
            {
                'title': 'Python Basics', 'content': 'Variables, loops, and conditionals — beginner-friendly!',
                'author': 'sophia', 'views': 0, 'timestamp': datetime.utcnow()
            },
        ]
        bookme_db.notes.insert_many(notes)
        print("Seeded demo notes")
    else:
        print("Notes already present, skipping seeding")


def seed_posts():
    if bookme_db.posts.count_documents({}) == 0:
        posts = [
            {
                'author': 'alice', 'text': 'Studying ML — gradient descent visualized 🧠📉', 'image': None,
                'likes': 0, 'comments': [], 'timestamp': datetime.utcnow().isoformat()
            },
            {
                'author': 'james', 'text': "Photosynthesis summary 🌿 — feel free to use!", 'image': None,
                'likes': 0, 'comments': [], 'timestamp': datetime.utcnow().isoformat()
            },
            {
                'author': 'sophia', 'text': 'Great group study session on Calculus today 🧮', 'image': None,
                'likes': 0, 'comments': [], 'timestamp': datetime.utcnow().isoformat()
            },
        ]
        bookme_db.posts.insert_many(posts)
        print("Seeded demo feed posts")
    else:
        print("Posts already present, skipping seeding")


def seed_sessions():
    if bookme_db.sessions.count_documents({}) == 0:
        now = datetime.utcnow()
        sessions = []
        for u in ['alice', 'james', 'sophia']:
            for i in range(5):
                sessions.append({
                    'user': u, 'duration': 25 * 60, 'subject': 'Math', 'mode': 'Pomodoro',
                    'timestamp': now - timedelta(days=i)
                })
        bookme_db.sessions.insert_many(sessions)
        print("Seeded demo study sessions")
    else:
        print("Sessions already present, skipping seeding")


def main():
    seed_users()
    seed_notes()
    seed_posts()
    seed_sessions()


if __name__ == '__main__':
    main()
