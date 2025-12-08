"""
Seed script to populate MongoDB with sample data for development/testing.
Populates: users, feed posts, notes (grouped by subjects), and followers.
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
from utils.auth import get_current_user_from_token, get_pepper_by_version, combine_password_and_pepper, ph, get_current_pepper_version
import random

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.bookme


def iso_days_ago(days: int):
    return (datetime.utcnow() - timedelta(days=days)).isoformat()


def clear_collections():
    """Clear existing data"""
    print("Clearing existing collections...")
    db.users.delete_many({})
    db.decks.delete_many({})
    db.posts.delete_many({})
    db.notes.delete_many({})
    db.sessions.delete_many({})
    print("✓ Collections cleared")


def seed_users():
    """Create sample users with study data and streaks"""
    print("\nSeeding users...")

    users = [
        {
            "id": 1,
            "username": "admin",
            "name": "Admin User",
            "email": "admin@example.com",
            "profile_pic": None,
            "studyData": {
                "streak": 50000,
                "lastLogin": iso_days_ago(0),
                "decks": ["1", "2"],
                "loginHistory": {iso_days_ago(1): 1, iso_days_ago(2): 1},
            },
            "followers": [],
            "following": [],
        },
        {
            "id": 2,
            "username": "student",
            "name": "Student User",
            "email": "student@example.com",
            "profile_pic": "https://ui-avatars.com/api/?name=Student+User&background=0D6EFD&color=fff&size=200",
            "studyData": {
                "streak": 2,
                "lastLogin": iso_days_ago(3),
                "decks": ["2"],
                "loginHistory": {iso_days_ago(3): 1, iso_days_ago(4): 1},
            },
            "followers": [],
            "following": [],
        },
        {
            "id": 3,
            "username": "teacher",
            "name": "Teacher User",
            "email": "teacher@example.com",
            "profile_pic": None,
            "studyData": {
                "streak": 400,
                "lastLogin": iso_days_ago(10),
                "decks": ["1"],
                "loginHistory": {iso_days_ago(10): 1, iso_days_ago(11): 1},
            },
            "followers": [],
            "following": [],
        },
        {
            "id": 4,
            "username": "alice_chen",
            "name": "Alice Chen",
            "email": "alice@bookme.com",
            "profile_pic": "https://i.pravatar.cc/150?img=5",
            "studyData": {
                "streak": 15,
                "lastLogin": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "totalStudyTime": 45000,  # in seconds
                "decks": ["1", "2", "3"],
            },
            "bio": "Computer Science major | ML enthusiast | Coffee addict ☕",
            "followers": ["james_miller", "sophia_nguyen", "liam_smith"],
            "following": ["james_miller", "emma_wilson", "noah_davis"],
        },
        {
            "id": 5,
            "username": "james_miller",
            "name": "James Miller",
            "email": "james@bookme.com",
            "profile_pic": "https://i.pravatar.cc/150?img=12",
            "studyData": {
                "streak": 8,
                "lastLogin": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                "totalStudyTime": 32000,
                "decks": [],
            },
            "bio": "Biology student 🧬 | Nature lover | Studying for med school",
            "followers": ["alice_chen", "sophia_nguyen"],
            "following": ["alice_chen", "emma_wilson", "olivia_brown"],
        },
        {
            "id": 6,
            "username": "sophia_nguyen",
            "name": "Sophia Nguyen",
            "email": "sophia@bookme.com",
            "profile_pic": "https://i.pravatar.cc/150?img=16",
            "studyData": {
                "streak": 23,
                "lastLogin": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                "totalStudyTime": 67000,
                "decks": [],
            },
            "bio": "Mathematics & Physics | Problem solver | Chess player ♟️",
            "followers": ["alice_chen", "james_miller", "liam_smith", "emma_wilson"],
            "following": ["alice_chen", "james_miller", "noah_davis"],
        },
        {
            "id": 7,
            "username": "liam_smith",
            "name": "Liam Smith",
            "email": "liam@bookme.com",
            "profile_pic": "https://i.pravatar.cc/150?img=8",
            "studyData": {
                "streak": 12,
                "lastLogin": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "totalStudyTime": 41000,
                "decks": [],
            },
            "bio": "Psychology major | Book recommendations welcome 📚",
            "followers": ["sophia_nguyen", "emma_wilson"],
            "following": ["alice_chen", "sophia_nguyen", "olivia_brown"],
        },
        {
            "id": 8,
            "username": "emma_wilson",
            "name": "Emma Wilson",
            "email": "emma@bookme.com",
            "profile_pic": "https://i.pravatar.cc/150?img=10",
            "studyData": {
                "streak": 19,
                "lastLogin": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                "totalStudyTime": 54000,
                "decks": [],
            },
            "bio": "Chemistry nerd ⚗️ | Lab enthusiast | Future researcher",
            "followers": ["james_miller", "liam_smith", "noah_davis"],
            "following": ["sophia_nguyen", "james_miller", "olivia_brown"],
        },
        {
            "id": 9,
            "username": "noah_davis",
            "name": "Noah Davis",
            "email": "noah@bookme.com",
            "profile_pic": "https://i.pravatar.cc/150?img=13",
            "studyData": {
                "streak": 6,
                "lastLogin": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "totalStudyTime": 28000,
                "decks": [],
            },
            "bio": "History buff 📜 | Aspiring teacher | Movie fan",
            "followers": ["alice_chen", "olivia_brown"],
            "following": ["emma_wilson", "liam_smith"],
        },
        {
            "id": 10,
            "username": "olivia_brown",
            "name": "Olivia Brown",
            "email": "olivia@bookme.com",
            "profile_pic": "https://i.pravatar.cc/150?img=9",
            "studyData": {
                "streak": 31,
                "lastLogin": datetime.utcnow().isoformat(),
                "totalStudyTime": 89000,
                "decks": [],
            },
            "bio": "Engineering student ⚙️ | CAD lover | Robotics club president",
            "followers": ["james_miller", "emma_wilson", "noah_davis"],
            "following": ["alice_chen", "sophia_nguyen"],
        },
    ]

    db.users.insert_many(users)
    print(f"✓ Seeded {len(users)} users")


def genHashedPassword(password:str) -> str:
    """Generate a hashed password with current pepper."""
    current_version = get_current_pepper_version()
    if not current_version:
        raise ValueError("Current pepper version not set in environment.")
    pepper = get_pepper_by_version(current_version)
    combined = combine_password_and_pepper(password, pepper)
    password_hash = ph.hash(combined)
    return password_hash
def addHashedPasswords():
    """Add hashed passwords to existing users for testing."""
    print("\nAdding hashed passwords to users...")
    users = db.users.find({})
    password_hash = genHashedPassword('password123')
    for user in users:
        current_version = get_current_pepper_version()
        db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'password_hash': password_hash, 'pepper_version': current_version}}
        )
    print("✓ Hashed passwords added to users")

def seed_decks():
    """Create sample Flashcard Decks"""
    print("\nSeeding Flashcard Decks...")

    decks = [
        {
            "id": "1",
            "name": "Spanish Basics",
            "summary": "Spanish flashcard deck.",
            "len": "3",
            "cards": {
                "1": {
                    "front": "Hola",
                    "back": "Hello",
                    "tags": ["greeting", "basic"],
                    "correct_count": 5,
                    "incorrect_count": 1,
                    "last_reviewed": iso_days_ago(1),
                    "ease": 2.8,
                    "interval": 3,
                    "repetitions": 2,
                },
                "2": {
                    "front": "Adiós",
                    "back": "Goodbye",
                    "tags": ["farewell", "basic"],
                    "correct_count": 3,
                    "incorrect_count": 2,
                    "last_reviewed": iso_days_ago(4),
                    "ease": 2.3,
                    "interval": 1,
                    "repetitions": 1,
                },
                "3": {
                    "front": "Gracias",
                    "back": "Thank you",
                    "tags": ["politeness", "basic"],
                    "correct_count": 10,
                    "incorrect_count": 0,
                    "last_reviewed": iso_days_ago(10),
                    "ease": 3.2,
                    "interval": 15,
                    "repetitions": 5,
                },
            },
        },
        {
            "id": "2",
            "name": "French Basics",
            "summary": "French flashcard deck.",
            "len": "3",
            "cards": {
                "1": {
                    "front": "Bonjour",
                    "back": "Hello",
                    "tags": ["greeting", "basic"],
                    "correct_count": 7,
                    "incorrect_count": 1,
                    "last_reviewed": iso_days_ago(2),
                    "ease": 2.9,
                    "interval": 5,
                    "repetitions": 3,
                },
                "2": {
                    "front": "Au revoir",
                    "back": "Goodbye",
                    "tags": ["farewell", "basic"],
                    "correct_count": 2,
                    "incorrect_count": 3,
                    "last_reviewed": iso_days_ago(7),
                    "ease": 2.1,
                    "interval": 0,
                    "repetitions": 0,
                },
                "3": {
                    "front": "Merci",
                    "back": "Thank you",
                    "tags": ["politeness", "basic"],
                    "correct_count": 12,
                    "incorrect_count": 0,
                    "last_reviewed": iso_days_ago(30),
                    "ease": 3.5,
                    "interval": 30,
                    "repetitions": 8,
                },
            },
        },
    ]
    db.decks.insert_many(decks)
    print(f"✓ Seeded {len(decks)} flashcard decks")


def seed_notes():
    """Create sample notes grouped by subjects"""
    print("\nSeeding notes...")

    notes = [
        # Mathematics notes
        {
            "title": "Calculus I - Derivatives Cheat Sheet",
            "subject": "Mathematics",
            "content": """# Derivative Rules Reference

## Basic Rules
- Power Rule: d/dx(x^n) = nx^(n-1)
- Constant Rule: d/dx(c) = 0
- Sum Rule: d/dx(f + g) = f' + g'
- Product Rule: d/dx(fg) = f'g + fg'
- Quotient Rule: d/dx(f/g) = (f'g - fg')/g²

## Trigonometric Derivatives
- d/dx(sin x) = cos x
- d/dx(cos x) = -sin x
- d/dx(tan x) = sec²x

Perfect for exam prep! 📐""",
            "author": "sophia_nguyen",
            "views": 45,
            "timestamp": datetime.utcnow() - timedelta(days=3),
            "likes": 12,
            "tags": ["calculus", "derivatives", "formulas"],
        },
        {
            "title": "Linear Algebra - Matrix Operations",
            "subject": "Mathematics",
            "content": """# Matrix Operations Guide

## Addition & Subtraction
Matrices must have same dimensions. Add/subtract corresponding elements.

## Multiplication
(m×n) × (n×p) = (m×p)
C[i,j] = Σ A[i,k] × B[k,j]

## Properties
- (AB)C = A(BC) - Associative
- A(B+C) = AB + AC - Distributive
- (AB)ᵀ = BᵀAᵀ - Transpose property

Great for linear systems! 🔢""",
            "author": "alice_chen",
            "views": 32,
            "timestamp": datetime.utcnow() - timedelta(days=5),
            "likes": 8,
            "tags": ["linear-algebra", "matrices"],
        },
        {
            "title": "Statistics - Probability Distributions",
            "subject": "Mathematics",
            "content": """# Common Probability Distributions

## Normal Distribution
- Bell curve, μ (mean), σ (std dev)
- 68-95-99.7 rule

## Binomial Distribution
- n trials, p probability
- P(X=k) = C(n,k) × p^k × (1-p)^(n-k)

## Poisson Distribution
- Rate λ over time/space
- P(X=k) = (λ^k × e^(-λ))/k!

Essential for hypothesis testing! 📊""",
            "author": "sophia_nguyen",
            "views": 28,
            "timestamp": datetime.utcnow() - timedelta(days=7),
            "likes": 6,
            "tags": ["statistics", "probability"],
        },
        # Biology notes
        {
            "title": "Cell Biology - Mitosis vs Meiosis",
            "subject": "Biology",
            "content": """# Cell Division Comparison

## Mitosis
- Produces 2 identical daughter cells
- Diploid → Diploid (2n → 2n)
- Stages: PMAT (Prophase, Metaphase, Anaphase, Telophase)
- Purpose: Growth, repair, asexual reproduction

## Meiosis
- Produces 4 unique gametes
- Diploid → Haploid (2n → n)
- Two divisions: Meiosis I & II
- Purpose: Sexual reproduction, genetic diversity

Key difference: Crossing over in Meiosis I! 🧬""",
            "author": "james_miller",
            "views": 67,
            "timestamp": datetime.utcnow() - timedelta(days=2),
            "likes": 18,
            "tags": ["cell-biology", "mitosis", "meiosis"],
        },
        {
            "title": "Photosynthesis Overview",
            "subject": "Biology",
            "content": """# Photosynthesis Process

## Light Reactions (Thylakoid)
1. Light absorption by chlorophyll
2. Water splitting (photolysis)
3. ATP & NADPH production
4. O₂ release

## Calvin Cycle (Stroma)
1. Carbon fixation (CO₂ + RuBP)
2. Reduction (using ATP & NADPH)
3. Regeneration of RuBP
4. Glucose production

Equation: 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂ 🌿""",
            "author": "james_miller",
            "views": 53,
            "timestamp": datetime.utcnow() - timedelta(days=4),
            "likes": 15,
            "tags": ["photosynthesis", "plant-biology"],
        },
        {
            "title": "Human Anatomy - Nervous System",
            "subject": "Biology",
            "content": """# Nervous System Overview

## Central Nervous System (CNS)
- Brain: Control center
- Spinal Cord: Information highway

## Peripheral Nervous System (PNS)
- Somatic: Voluntary movement
- Autonomic: Involuntary functions
  * Sympathetic: Fight or flight
  * Parasympathetic: Rest and digest

## Neuron Structure
Dendrites → Cell Body → Axon → Synaptic Terminals

Action potential travels at 100 m/s! ⚡""",
            "author": "emma_wilson",
            "views": 41,
            "timestamp": datetime.utcnow() - timedelta(days=6),
            "likes": 11,
            "tags": ["anatomy", "nervous-system"],
        },
        # Programming notes
        {
            "title": "Python Basics - Data Structures",
            "subject": "Programming",
            "content": """# Python Data Structures Guide

## Lists (Mutable, Ordered)
```python
my_list = [1, 2, 3, 4]
my_list.append(5)
my_list[0] = 10
```

## Tuples (Immutable, Ordered)
```python
my_tuple = (1, 2, 3)
x, y, z = my_tuple  # unpacking
```

## Dictionaries (Key-Value Pairs)
```python
my_dict = {'name': 'Alice', 'age': 20}
my_dict['major'] = 'CS'
```

## Sets (Unique, Unordered)
```python
my_set = {1, 2, 3}
my_set.add(4)
```

Choose the right tool for the job! 💻""",
            "author": "alice_chen",
            "views": 89,
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "likes": 24,
            "tags": ["python", "data-structures"],
        },
        {
            "title": "JavaScript ES6 Features",
            "subject": "Programming",
            "content": """# Modern JavaScript Features

## Arrow Functions
```javascript
const add = (a, b) => a + b;
```

## Destructuring
```javascript
const {name, age} = person;
const [first, second] = array;
```

## Template Literals
```javascript
const message = `Hello, ${name}!`;
```

## Spread Operator
```javascript
const newArr = [...oldArr, 4, 5];
```

## Async/Await
```javascript
const data = await fetchData();
```

Makes code cleaner and more readable! 🚀""",
            "author": "alice_chen",
            "views": 76,
            "timestamp": datetime.utcnow() - timedelta(days=3),
            "likes": 19,
            "tags": ["javascript", "es6"],
        },
        {
            "title": "Git Workflow Essentials",
            "subject": "Programming",
            "content": """# Git Commands You Need

## Basic Workflow
```bash
git status              # Check changes
git add .               # Stage all files
git commit -m "message" # Commit changes
git push origin main    # Push to remote
```

## Branching
```bash
git branch feature      # Create branch
git checkout feature    # Switch branch
git merge feature       # Merge branch
```

## Undoing Changes
```bash
git reset HEAD~1        # Undo last commit
git checkout -- file    # Discard changes
git revert commit-hash  # Revert commit
```

Version control made easy! 🌿""",
            "author": "olivia_brown",
            "views": 62,
            "timestamp": datetime.utcnow() - timedelta(days=5),
            "likes": 16,
            "tags": ["git", "version-control"],
        },
        # Psychology notes
        {
            "title": "Cognitive Psychology - Memory Types",
            "subject": "Psychology",
            "content": """# Memory Systems

## Sensory Memory
- Duration: < 1 second
- Capacity: Large but brief
- Types: Iconic (visual), Echoic (auditory)

## Short-Term Memory (STM)
- Duration: 15-30 seconds
- Capacity: 7±2 items (Miller's Law)
- Working memory processes info

## Long-Term Memory (LTM)
- Duration: Unlimited
- Capacity: Unlimited
- Types:
  * Explicit (conscious): Episodic, Semantic
  * Implicit (unconscious): Procedural, Priming

Rehearsal moves STM → LTM! 🧠""",
            "author": "liam_smith",
            "views": 38,
            "timestamp": datetime.utcnow() - timedelta(days=4),
            "likes": 10,
            "tags": ["cognitive-psychology", "memory"],
        },
        {
            "title": "Developmental Psychology - Piaget's Stages",
            "subject": "Psychology",
            "content": """# Piaget's Cognitive Development Stages

## 1. Sensorimotor (0-2 years)
- Object permanence develops
- Learn through senses and actions

## 2. Preoperational (2-7 years)
- Symbolic thinking
- Egocentrism
- No conservation concept

## 3. Concrete Operational (7-11 years)
- Logical thinking about concrete events
- Conservation mastered
- Classification skills

## 4. Formal Operational (12+ years)
- Abstract reasoning
- Hypothetical thinking
- Metacognition

Each stage builds on the previous! 👶""",
            "author": "liam_smith",
            "views": 44,
            "timestamp": datetime.utcnow() - timedelta(days=6),
            "likes": 12,
            "tags": ["developmental-psychology", "piaget"],
        },
        # Chemistry notes
        {
            "title": "Organic Chemistry - Functional Groups",
            "subject": "Chemistry",
            "content": """# Common Functional Groups

## Alcohols (-OH)
- Nomenclature: -ol suffix
- Example: Ethanol (CH₃CH₂OH)
- Properties: Polar, H-bonding

## Carboxylic Acids (-COOH)
- Nomenclature: -oic acid suffix
- Example: Acetic acid (CH₃COOH)
- Properties: Acidic, polar

## Ketones (C=O)
- Nomenclature: -one suffix
- Example: Acetone (CH₃COCH₃)
- Properties: Polar, good solvents

## Amines (-NH₂)
- Nomenclature: -amine suffix
- Example: Methylamine (CH₃NH₂)
- Properties: Basic, polar

Recognition is key! ⚗️""",
            "author": "emma_wilson",
            "views": 51,
            "timestamp": datetime.utcnow() - timedelta(days=2),
            "likes": 14,
            "tags": ["organic-chemistry", "functional-groups"],
        },
        {
            "title": "Chemical Equilibrium Concepts",
            "subject": "Chemistry",
            "content": """# Equilibrium Principles

## Le Chatelier's Principle
System shifts to oppose change:
- Add reactant → shifts right
- Increase pressure → favors fewer moles
- Increase temp → favors endothermic direction

## Equilibrium Constant (K)
K = [Products]/[Reactants]
- K > 1: Products favored
- K < 1: Reactants favored
- K = 1: Equal amounts

## ICE Tables
Initial, Change, Equilibrium
Helps solve equilibrium problems!

Practice makes perfect! ⚖️""",
            "author": "emma_wilson",
            "views": 47,
            "timestamp": datetime.utcnow() - timedelta(days=5),
            "likes": 13,
            "tags": ["chemistry", "equilibrium"],
        },
        # Physics notes
        {
            "title": "Classical Mechanics - Newton's Laws",
            "subject": "Physics",
            "content": """# Newton's Three Laws

## First Law (Inertia)
Object at rest stays at rest, object in motion stays in motion
Unless acted upon by external force

## Second Law (F = ma)
Force = Mass × Acceleration
Explains how forces affect motion

## Third Law (Action-Reaction)
For every action, equal and opposite reaction
Forces always come in pairs

## Applications
- First: Seatbelts in cars
- Second: Rocket propulsion
- Third: Walking, swimming

Foundation of classical mechanics! 🚀""",
            "author": "sophia_nguyen",
            "views": 55,
            "timestamp": datetime.utcnow() - timedelta(days=3),
            "likes": 15,
            "tags": ["physics", "mechanics", "newton"],
        },
        {
            "title": "Electricity & Magnetism Basics",
            "subject": "Physics",
            "content": """# E&M Fundamentals

## Electric Field (E)
E = F/q = kQ/r²
Direction: Away from + charge, toward - charge

## Magnetic Field (B)
Created by moving charges (currents)
Force on charge: F = qvB sin(θ)

## Ohm's Law
V = IR
- V: Voltage (Volts)
- I: Current (Amperes)
- R: Resistance (Ohms)

## Power
P = IV = I²R = V²/R

Essential for circuits! ⚡""",
            "author": "olivia_brown",
            "views": 49,
            "timestamp": datetime.utcnow() - timedelta(days=4),
            "likes": 13,
            "tags": ["physics", "electricity", "magnetism"],
        },
    ]

    db.notes.insert_many(notes)
    print(f"✓ Seeded {len(notes)} notes across subjects")


def seed_posts():
    """Create sample feed posts"""
    print("\nSeeding feed posts...")

    posts = [
        {
            "author": "alice_chen",
            "text": "Just finished implementing a neural network from scratch! The satisfaction of seeing it converge is unreal 🤖✨ #MachineLearning #AI",
            "image": None,
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "likes": 23,
            "comments": [
                {
                    "author": "james_miller",
                    "text": "That's awesome! Did you use numpy or pure Python?",
                    "timestamp": datetime.utcnow() - timedelta(hours=1),
                },
                {
                    "author": "sophia_nguyen",
                    "text": "Amazing work! Would love to see your code 👀",
                    "timestamp": datetime.utcnow() - timedelta(minutes=45),
                },
            ],
        },
        {
            "author": "james_miller",
            "text": "Study tip: The Pomodoro Technique changed my life! 25 min focus + 5 min break = productivity heaven 🍅⏰",
            "image": "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=800&auto=format&fit=crop",
            "timestamp": datetime.utcnow() - timedelta(hours=5),
            "likes": 18,
            "comments": [
                {
                    "author": "liam_smith",
                    "text": "Been using this for months, absolute game changer!",
                    "timestamp": datetime.utcnow() - timedelta(hours=4),
                }
            ],
        },
        {
            "author": "sophia_nguyen",
            "text": "Calculus exam tomorrow. Coffee count: 4. Confidence level: 📈 Let's do this! 💪☕",
            "image": None,
            "timestamp": datetime.utcnow() - timedelta(hours=8),
            "likes": 31,
            "comments": [
                {
                    "author": "alice_chen",
                    "text": "You've got this! Your derivative notes helped me so much!",
                    "timestamp": datetime.utcnow() - timedelta(hours=7),
                },
                {
                    "author": "emma_wilson",
                    "text": "Good luck! Remember to breathe 🌟",
                    "timestamp": datetime.utcnow() - timedelta(hours=6),
                },
                {
                    "author": "liam_smith",
                    "text": "Crush it! 🔥",
                    "timestamp": datetime.utcnow() - timedelta(hours=5),
                },
            ],
        },
        {
            "author": "liam_smith",
            "text": "Just finished 'Atomic Habits' by James Clear. Honestly one of the best books on productivity and habit formation. Highly recommend! 📚✨",
            "image": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=800&auto=format&fit=crop",
            "timestamp": datetime.utcnow() - timedelta(hours=12),
            "likes": 15,
            "comments": [],
        },
        {
            "author": "emma_wilson",
            "text": "Lab day! Today we're synthesizing aspirin from salicylic acid. The smell is... interesting 😅⚗️ #ChemistryLife",
            "image": "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800&auto=format&fit=crop",
            "timestamp": datetime.utcnow() - timedelta(hours=15),
            "likes": 27,
            "comments": [
                {
                    "author": "james_miller",
                    "text": "Love lab days! Be careful with the acetic anhydride!",
                    "timestamp": datetime.utcnow() - timedelta(hours=14),
                }
            ],
        },
        {
            "author": "noah_davis",
            "text": "Hot take: History is just pattern recognition at scale. Once you see the patterns, everything clicks 🧩🌍",
            "image": None,
            "timestamp": datetime.utcnow() - timedelta(hours=20),
            "likes": 12,
            "comments": [
                {
                    "author": "sophia_nguyen",
                    "text": "Same with math! It's all about recognizing patterns",
                    "timestamp": datetime.utcnow() - timedelta(hours=19),
                }
            ],
        },
        {
            "author": "olivia_brown",
            "text": "Spent 6 hours debugging... turns out it was a missing semicolon. I hate programming. Also I love programming. It's complicated 😭💻",
            "image": None,
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "likes": 42,
            "comments": [
                {
                    "author": "alice_chen",
                    "text": "THE STRUGGLE IS REAL 😂",
                    "timestamp": datetime.utcnow() - timedelta(hours=22),
                },
                {
                    "author": "noah_davis",
                    "text": "This is why I switched to Python lol",
                    "timestamp": datetime.utcnow() - timedelta(hours=21),
                },
                {
                    "author": "olivia_brown",
                    "text": "Python has its own special pain though 😅",
                    "timestamp": datetime.utcnow() - timedelta(hours=20),
                },
            ],
        },
        {
            "author": "sophia_nguyen",
            "text": "Quick study session turned into a 4-hour deep dive into quantum mechanics. No regrets. The universe is WEIRD 🌌⚛️",
            "image": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=800&auto=format&fit=crop",
            "timestamp": datetime.utcnow() - timedelta(days=1, hours=6),
            "likes": 19,
            "comments": [
                {
                    "author": "emma_wilson",
                    "text": "Quantum is mind-blowing! Wave-particle duality still breaks my brain",
                    "timestamp": datetime.utcnow() - timedelta(days=1, hours=5),
                }
            ],
        },
        {
            "author": "james_miller",
            "text": "Group study session was lit! Thanks @alice_chen @sophia_nguyen for explaining meiosis like I'm 5. Finally get it! 🧬🎉",
            "image": None,
            "timestamp": datetime.utcnow() - timedelta(days=2),
            "likes": 21,
            "comments": [
                {
                    "author": "alice_chen",
                    "text": "Anytime! Teaching helps me learn better too",
                    "timestamp": datetime.utcnow() - timedelta(days=1, hours=23),
                }
            ],
        },
        {
            "author": "emma_wilson",
            "text": "Friendly reminder: Take breaks! Your brain needs rest to consolidate information. Self-care is study care 💙🧘‍♀️",
            "image": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800&auto=format&fit=crop",
            "timestamp": datetime.utcnow() - timedelta(days=2, hours=8),
            "likes": 35,
            "comments": [
                {
                    "author": "liam_smith",
                    "text": "Needed to hear this today. Thank you! 🙏",
                    "timestamp": datetime.utcnow() - timedelta(days=2, hours=7),
                },
                {
                    "author": "sophia_nguyen",
                    "text": "So true! Sleep is when your brain does the real learning",
                    "timestamp": datetime.utcnow() - timedelta(days=2, hours=6),
                },
            ],
        },
        {
            "author": "alice_chen",
            "text": "Pro tip: Explain concepts out loud like you're teaching someone. If you can't explain it simply, you don't understand it well enough. - Einstein (probably) 🗣️💡",
            "image": None,
            "timestamp": datetime.utcnow() - timedelta(days=3),
            "likes": 28,
            "comments": [
                {
                    "author": "olivia_brown",
                    "text": "Rubber duck debugging but for studying! Love it",
                    "timestamp": datetime.utcnow() - timedelta(days=2, hours=22),
                }
            ],
        },
        {
            "author": "olivia_brown",
            "text": "Robotics club presentation went amazing! Our autonomous rover can navigate obstacles and we're heading to regionals! 🤖🏆",
            "image": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&auto=format&fit=crop",
            "timestamp": datetime.utcnow() - timedelta(days=3, hours=12),
            "likes": 44,
            "comments": [
                {
                    "author": "alice_chen",
                    "text": "Congrats! That's incredible! 🎉",
                    "timestamp": datetime.utcnow() - timedelta(days=3, hours=10),
                },
                {
                    "author": "noah_davis",
                    "text": "So proud of you! Can't wait to see it compete",
                    "timestamp": datetime.utcnow() - timedelta(days=3, hours=9),
                },
            ],
        },
    ]

    db.posts.insert_many(posts)
    print(f"✓ Seeded {len(posts)} feed posts")


def seed_study_sessions():
    """Create sample study sessions"""
    print("\nSeeding study sessions...")

    users = [
        "alice_chen",
        "james_miller",
        "sophia_nguyen",
        "liam_smith",
        "emma_wilson",
        "noah_davis",
        "olivia_brown",
    ]
    subjects = [
        "Mathematics",
        "Biology",
        "Programming",
        "Chemistry",
        "Physics",
        "Psychology",
    ]
    modes = ["Pomodoro", "Deep Focus", "Quick Review", "Flashcards"]

    sessions = []
    for _ in range(50):
        user = random.choice(users)
        sessions.append(
            {
                "user": user,
                "duration": random.randint(900, 7200),  # 15 min to 2 hours
                "subject": random.choice(subjects),
                "mode": random.choice(modes),
                "timestamp": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            }
        )

    db.sessions.insert_many(sessions)
    print(f"✓ Seeded {len(sessions)} study sessions")


def main():
    print("=" * 60)
    print("MongoDB Seeding Script - BookMe")
    print("=" * 60)

    clear_collections()
    seed_users()
    seed_decks()
    seed_notes()
    seed_posts()
    seed_study_sessions()

    print("\n" + "=" * 60)
    print("✓ Database seeding completed successfully!")
    print("=" * 60)
    print("\nData Summary:")
    print(f"  Users: {db.users.count_documents({})}")
    print("  #Adding user's Hashed Passwords")
    addHashedPasswords()
    print(f"  Decks: {db.decks.count_documents({})}")
    print(f"  Notes: {db.notes.count_documents({})}")
    print(f"  Posts: {db.posts.count_documents({})}")
    print(f"  Study Sessions: {db.sessions.count_documents({})}")
    print("\nYou can now view the data at:")
    print("  - Community (Notes): http://localhost:5000/community/")
    print("  - Friends: http://localhost:5000/friends/")
    print("  - Feed: http://localhost:5000/feed/")
    print("=" * 60)


if __name__ == "__main__":
    main()
