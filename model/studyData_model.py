from .login_model import USERS, get_user_by_username
"""
Login model with hardcoded user data for teaching purposes.
No database connection required.
"""
DECKS = {1: {'name': 'Spanish Basics', 'cards': ['Hola - Hello', 'Adiós - Goodbye', 'Gracias - Thank you']},
         2: {'name': 'French Basics', 'cards': ['Bonjour - Hello', 'Au revoir - Goodbye', 'Merci - Thank you']}}

def get_deck_by_id(deck_id):
    """
    Retrieve a deck by its ID from the hardcoded decks.
    
    Args:
        deck_id (int): The ID of the deck to retrieve"""
    return DECKS.get(deck_id, None)

def get_user_study_data(username):
    """
    Retrieve study data for a given user.
    
    Args:
        username (str): The username of the user"""
    user = get_user_by_username(username)
    if user and 'studyData' in user:
        return user['studyData']
    return None
