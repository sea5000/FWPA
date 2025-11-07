"""
Login model with hardcoded user data for teaching purposes.
No database connection required.
"""
# Hardcoded users list
USERS = [{
        'id': 1,
        'username': 'admin',
        'password': 'admin123',
        'name': 'Admin',
        'email': 'admin@example.com',
        'studyData': {'streak': 50000, 'lastLogin': '2024-06-01', 'decks': [1,2] }
    },
    {
        'id': 2,
        'username': 'student',
        'password': 'student123',
        'name': 'Student',
        'email': 'student@example.com',
        'studyData': {'streak': 2, 'lastLogin': '2024-06-01', 'decks': [2] }
    },
    {
        'id': 3,
        'username': 'teacher',
        'password': 'teacher123',
        'name': 'Teacher',
        'email': 'teacher@example.com',
        'studyData': {'streak': 400, 'lastLogin': '2024-06-01', 'decks': [1] }
    }
]


def get_user_by_username(username):
    """
    Retrieve a user by username from the hardcoded list.
    
    Args:
        username (str): The username to search for
        
    Returns:
        dict: User dictionary if found, None otherwise
    """
    for user in USERS:
        if user['username'] == username:
            return user
    return None


def verify_user(username, password):
    """
    Verify if the username and password match a user in the list.
    
    Args:
        username (str): The username to verify
        password (str): The password to verify
        
    Returns:
        dict: User dictionary if credentials are correct, None otherwise
    """
    user = get_user_by_username(username)
    if user and user['password'] == password:
        # Return user without password for security
        return {
            'id': user['id'],
            'username': user['username'],
            'email': user['email']
        }
    return None


def get_all_users():
    """
    Get all users (without passwords) from the hardcoded list.
    
    Returns:
        list: List of user dictionaries without passwords
    """
    return [
        {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'password': user['password']
        }
        for user in USERS
    ]
