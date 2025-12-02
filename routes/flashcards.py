from flask import Blueprint, render_template, g, request, abort, redirect, url_for
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from model.studyData_model import get_user_decks, get_user_study_data, get_deck, update_card, add_card, delete_card, record_review, create_deck, add_deck_to_user, get_deck_by_id, update_deckInfo, delete_deck
from flask import jsonify


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
    deck_obj = get_deck_by_id(deck_id)
    if not deck_obj:
        return render_template('404.html'), 404
    return render_template('flashcard_deck.html', username=g.current_user, users=get_all_users(), deck=deck_obj, deck_id=deck_id)

@flashcards_bp.route('/<deck_id>/delete', endpoint='delete', methods=['POST'])
def flashcards_delete(deck_id):
    """Delete a deck by its ID."""
    success = delete_deck(deck_id)
    if not success:
        return render_template('404.html'), 404
    return redirect(url_for('flashcards.index'))

@flashcards_bp.route('/<deck_id>/stats', endpoint='stats', methods=['GET'])
def flashcards_stats(deck_id):
    # return JSON stats for use by JavaScript
    deck_obj = get_deck_by_id(deck_id)
    if not deck_obj:
        return jsonify({'ok': False, 'error': 'deck not found'}), 404

    # normalize cards mapping (cards may be stored as dicts or objects)
    cards_map = deck_obj.get('cards', {}) if isinstance(deck_obj, dict) else getattr(deck_obj, 'cards', {}) or {}
    total_cards = len(cards_map)
    total_correct = 0
    total_incorrect = 0

    cards_list = []
    for key, card in cards_map.items():
        # card may be dict or object
        if isinstance(card, dict):
            front = card.get('front')
            back = card.get('back')
            correct_count = int(card.get('correct_count', 0))
            incorrect_count = int(card.get('incorrect_count', 0))
        else:
            front = getattr(card, 'front', None)
            back = getattr(card, 'back', None)
            correct_count = int(getattr(card, 'correct_count', 0) or 0)
            incorrect_count = int(getattr(card, 'incorrect_count', 0) or 0)

        total_correct += correct_count
        total_incorrect += incorrect_count

        cards_list.append({
            'id': str(key),
            'front': front,
            'back': back,
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
        })

    stats = {
        'total_cards': total_cards,
        'total_correct': total_correct,
        'total_incorrect': total_incorrect,
    }

    deck_meta = {
        'id': deck_id,
        'name': deck_obj.get('name') if isinstance(deck_obj, dict) else getattr(deck_obj, 'name', None)
    }

    return jsonify({'deck': deck_meta, 'stats': stats, 'cards': cards_list})

@flashcards_bp.route('/<deck_id>/edit', endpoint='edit', methods=['GET', 'POST'])
def flashcards_edit(deck_id):
    """Edit a deck: show the edit UI and accept POSTed updates. For now, render the template and leave full save logic for later."""
    from model.studyData_model import get_deck_by_id
    deck_obj = get_deck_by_id(deck_id)
    if not deck_obj:
        return render_template('404.html'), 404
    if request.method == 'POST':
        form = request.form
        # existing cards
        existing_cards = list(deck_obj.get('cards', {}).keys()) if isinstance(deck_obj, dict) else list(getattr(deck_obj, 'cards', {}).keys())
        for cardn in existing_cards:
            card_key = str(cardn)
            # deletion checkbox
            if form.get(f'delete_{card_key}'):
                delete_card(deck_id, card_key)
                continue

            front = form.get(f'front_{card_key}')
            back = form.get(f'back_{card_key}')
            if front is None or back is None:
                continue
            # compare with current values
            cur = deck_obj.get('cards', {}).get(cardn) if isinstance(deck_obj, dict) else getattr(deck_obj, 'cards', {}).get(cardn)
            cur_front = cur.get('front') if isinstance(cur, dict) else getattr(cur, 'front', None)
            cur_back = cur.get('back') if isinstance(cur, dict) else getattr(cur, 'back', None)
            if front != cur_front or back != cur_back:
                update_card(deck_id, card_key, front, back)

        # new cards arrays
        if form.get('deck_name'):
            update_deckInfo(deck_id, name=form.get('deck_name'))
        if form.get('deck_summary'):
            update_deckInfo(deck_id, summary=form.get('deck_summary'))

        new_fronts = form.getlist('new_front[]')
        new_backs = form.getlist('new_back[]')
        for f, b in zip(new_fronts, new_backs):
            if not f and not b:
                continue
            add_card(deck_id, f, b)

        return redirect(url_for('flashcards.edit', deck_id=deck_id))

    return render_template('flashcard_edit.html', username=g.current_user, users=get_all_users(), deck=deck_obj, deck_id=deck_id)

@flashcards_bp.route('/<deck_id>/study', endpoint='study')
def flashcards_study(deck_id):
    #deck_id = request.args.get('deck_id')
    print(deck_id)
    if not deck_id:
        abort(400)
    return render_template('flashcard_study.html', username=g.current_user, users=get_all_users(), deck=get_deck(deck_id), deck_id=deck_id)

@flashcards_bp.route('/study/review', methods=['POST'])
def flashcards_review():
    """Accept review results and call Card.review on the server-side card instance.

    Expects JSON or form data with: deck_id, card_id, correct (true/false or 1/0).
    Returns JSON with the updated card review info.
    """
    data = request.get_json(silent=True) or request.form
    deck_id = data.get('deck_id')
    card_id = data.get('card_id')
    correct = data.get('correct')
    if deck_id is None or card_id is None or correct is None:
        return jsonify({'ok': False, 'error': 'missing parameters'}), 400

    # normalize correct
    if isinstance(correct, str):
        correct_val = correct.lower() in ('1', 'true', 'yes', 'on')
    else:
        correct_val = bool(correct)

    deck = get_deck(deck_id)
    if not deck:
        return jsonify({'ok': False, 'error': 'deck not found'}), 404

    # find matching card key (cards keys may be int or str)
    found_key = None
    for k in deck.get('cards', {}).keys():
        if str(k) == str(card_id):
            found_key = str(k)
            break

    if not found_key:
        return jsonify({'ok': False, 'error': 'card not found'}), 404

    updated = record_review(deck_id, found_key, correct_val)
    if not updated:
        return jsonify({'ok': False, 'error': 'failed to record review'}), 500
    return jsonify({'ok': True, 'result': updated})
 

@flashcards_bp.route('/new_deck',endpoint='new_deck', methods=['get'])
def flashcards_new_deck():
    """Render the new deck creation page (form)."""
    # create_deck(name, summary) -> create a new deck record and persist it
    deck = create_deck("New Deck", "")
    # attach the newly-created deck to the current user's studyData
    add_deck_to_user(g.current_user, deck['id'])
    return redirect(url_for('flashcards.edit', deck_id = deck['id']))
