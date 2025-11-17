from flask import Blueprint, render_template, g, request, abort, redirect, url_for
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from model.studyData_model import get_user_decks, get_user_study_data, get_deck, update_card, add_card, delete_card


flashcards_bp = Blueprint('flashcards', __name__)


@flashcards_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@flashcards_bp.route('/', endpoint='index')
def flashcards_index():
    # userDecks = get_user_decks(g.current_user)
    return render_template('flashcards.html', username=g.current_user, users=get_all_users(), decks=get_user_decks(g.current_user), studyData=get_user_study_data(g.current_user))
    
@flashcards_bp.route('/<deck_id>/', endpoint='deck')
def flashcards_deck(deck_id):
    """Show a single deck's cards (deck view)."""
    from model.studyData_model import get_deck_by_id
    deck_obj = get_deck_by_id(deck_id)
    if not deck_obj:
        return render_template('404.html'), 404
    return render_template('flashcard_deck.html', username=g.current_user, users=get_all_users(), deck=deck_obj, deck_id=deck_id)

@flashcards_bp.route('/<deck_id>/stats', endpoint='stats')
def flashcards_stats(deck_id):
    """Show basic statistics for a deck. (placeholder for richer Anki-like stats)
    """
    from model.studyData_model import get_deck_by_id
    deck_obj = get_deck_by_id(deck_id)
    if not deck_obj:
        return render_template('404.html'), 404

    # compute simple stats from Card objects
    total_cards = len(deck_obj.cards)
    total_correct = sum(getattr(c, 'correct_count', 0) for c in deck_obj.cards.values())
    total_incorrect = sum(getattr(c, 'incorrect_count', 0) for c in deck_obj.cards.values())

    stats = {
        'total_cards': total_cards,
        'total_correct': total_correct,
        'total_incorrect': total_incorrect,
    }

    return render_template('flashcard_stats.html', username=g.current_user, users=get_all_users(), deck=deck_obj, stats=stats)

@flashcards_bp.route('/<deck_id>/edit', endpoint='edit', methods=['GET', 'POST'])
def flashcards_edit(deck_id):
    """Edit a deck: show the edit UI and accept POSTed updates. For now, render the template and leave full save logic for later."""
    from model.studyData_model import get_deck_by_id
    deck_obj = get_deck_by_id(deck_id)
    if not deck_obj:
        return render_template('404.html'), 404

    # TODO: implement POST handling to update/add/delete cards
    return render_template('flashcard_edit.html', username=g.current_user, users=get_all_users(), deck=deck_obj, deck_id=deck_id)
 