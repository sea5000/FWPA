from flask import Blueprint, render_template, g, request, abort, redirect, url_for
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from model.studyData_model import get_user_permissions, get_user_decks, get_user_study_data, get_deck, update_card, add_card, delete_card, record_review, create_deck, add_deck_to_user, get_deck_by_id, update_deckInfo, delete_deck, add_deck_permissions, rem_deck_permissions, get_friends, get_deck_permissions
from flask import jsonify
from functools import wraps


flashcards_bp = Blueprint('flashcards', __name__)


def require_edit_permission(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # determine deck_id from kwargs or positional args
        deck_id = kwargs.get('deck_id') if 'deck_id' in kwargs else (args[0] if args else None)
        if not deck_id:
            abort(400)

        # permissions for current user (may return deck_id lists under 'editor'/'editor(s)')
        perms = get_user_permissions(g.current_user)
        if not perms:
            abort(403)

        editors = perms.get('editors') or perms.get('editor') or []
        owners = perms.get('owner') or []

        allowed = False
        # editors may be a list of usernames or a list of deck_ids
        if isinstance(editors, list):
            if g.current_user in editors or str(deck_id) in editors:
                allowed = True

        # owners may be a list of deck_ids (or usernames in some schemas)
        if isinstance(owners, list):
            if g.current_user in owners or str(deck_id) in owners:
                allowed = True

        # also check deck's owner field directly
        if not allowed:
            deck = get_deck_by_id(deck_id)
            if deck and deck.get('owner') == g.current_user:
                allowed = True

        if not allowed:
            abort(403)

        return fn(*args, **kwargs)

    return wrapper


def require_review_permission(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # determine deck_id from kwargs or positional args
        deck_id = kwargs.get('deck_id') if 'deck_id' in kwargs else (args[0] if args else None)
        if not deck_id:
            abort(400)

        # permissions for current user (may return deck_id lists under 'editor'/'editor(s)')
        perms = get_user_permissions(g.current_user)
        if not perms:
            abort(403)

        editors = perms.get('reviewer') or perms.get('reviewer') or []
        owners = perms.get('owner') or []

        allowed = False
        # editors may be a list of usernames or a list of deck_ids
        if isinstance(editors, list):
            if g.current_user in editors or str(deck_id) in editors:
                allowed = True

        # owners may be a list of deck_ids (or usernames in some schemas)
        if isinstance(owners, list):
            if g.current_user in owners or str(deck_id) in owners:
                allowed = True

        # also check deck's owner field directly
        if not allowed:
            deck = get_deck_by_id(deck_id)
            if deck and deck.get('owner') == g.current_user:
                allowed = True

        if not allowed:
            abort(403)

        return fn(*args, **kwargs)

    return wrapper

@flashcards_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@flashcards_bp.route('/', endpoint='index')
def flashcards_index():
    # userDecks = get_user_decks(g.current_user)
    return render_template('flashcards.html', username=g.current_user, users=get_all_users(), decks=get_user_decks(g.current_user), permissions=get_user_permissions(g.current_user), studyData=get_user_study_data(g.current_user))

@flashcards_bp.route('/<deck_id>/', endpoint='deck')
@require_review_permission
def flashcards_deck(deck_id):
    """Show a single deck's cards (deck view)."""
    deck_obj = get_deck_by_id(deck_id)
    if not deck_obj:
        return render_template('404.html'), 404
    return render_template('flashcard_deck.html', username=g.current_user, users=get_all_users(), deck=deck_obj, deck_id=deck_id, studyData=get_user_study_data(g.current_user))

@flashcards_bp.route('/<deck_id>/delete', endpoint='delete', methods=['POST'])
@require_edit_permission
def flashcards_delete(deck_id):
    """Delete a deck by its ID."""
    success = delete_deck(deck_id)
    if not success:
        return render_template('404.html'), 404
    return redirect(url_for('flashcards.index'))

@flashcards_bp.route('/<deck_id>/stats', endpoint='stats', methods=['GET'])
@require_review_permission
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
@require_edit_permission
def flashcards_edit(deck_id):
    """Edit a deck: show the edit UI and accept POSTed updates. For now, render the template and leave full save logic for later."""
    from model.studyData_model import get_deck_by_id
    deck_obj = get_deck_by_id(deck_id)
    if not deck_obj:
        return render_template('404.html'), 404
    # get friend profiles via model helper
    friends = get_friends(g.current_user)
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

    return render_template('flashcard_edit.html', username=g.current_user, users=get_all_users(), deck=deck_obj, deck_id=deck_id, friends=friends, studyData=get_user_study_data(g.current_user))

@flashcards_bp.route('/<deck_id>/study', endpoint='study')
@require_review_permission
def flashcards_study(deck_id):
    #deck_id = request.args.get('deck_id')
    print(deck_id)
    if not deck_id:
        abort(400)
    return render_template('flashcard_study.html', username=g.current_user, users=get_all_users(), permissions=get_user_permissions(g.current_user), deck=get_deck(deck_id), deck_id=deck_id, studyData=get_user_study_data(g.current_user))

@flashcards_bp.route('/study/review', methods=['POST'])
@require_review_permission
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
    deck = create_deck("New Deck", "Summary goes here", g.current_user)
    # attach the newly-created deck to the current user's studyData
    add_deck_to_user(g.current_user, deck['id'])
    return redirect(url_for('flashcards.edit', deck_id = deck['id']))


@flashcards_bp.route('/<deck_id>/share', methods=['POST'])
@require_edit_permission
def flashcards_share(deck_id):
    """Accepts JSON payload of shares and updates permissions.

    Expected body: { shares: [ { username: 'alice', editor: true, reviewer: false }, ... ] }
    """
    data = request.get_json(silent=True)
    if not data or 'shares' not in data:
        return jsonify({'ok': False, 'error': 'missing shares payload'}), 400

    shares = data.get('shares')
    results = []
    for entry in shares:
        uname = entry.get('username')
        if not uname:
            continue
        # editors
        if entry.get('editor'):
            add_deck_permissions(deck_id, 'editors', uname)
        else:
            rem_deck_permissions(deck_id, 'editors', uname)

        # reviewers
        if entry.get('reviewer'):
            add_deck_permissions(deck_id, 'reviewers', uname)
        else:
            rem_deck_permissions(deck_id, 'reviewers', uname)

        results.append({'username': uname, 'ok': True})

    return jsonify({'ok': True, 'results': results})


@flashcards_bp.route('/<deck_id>/permissions', methods=['GET'])
@require_edit_permission
def flashcards_permissions(deck_id):
    perm = get_deck_permissions(deck_id)
    print(perm)
    perm['editors'].remove('admin')
    perm['reviewers'].remove('admin') 
    if not perm:
        return jsonify({'ok': False, 'error': 'not found'}), 404
    return jsonify({'ok': True, 'permissions': perm})

@flashcards_bp.route('/userlist', methods=['GET'])
def returnUserList():
    """Designed for getting a list of usrs to share flashcard decks with, returns a list of users from the database, and adds the 'all' for all users. Returns a list. """
    users = get_all_users() or []
    # get_all_users returns list of user dicts; normalize to usernames
    usernames = []
    seen = set()
    for u in users:
        name = None
        try:
            # u may be dict-like
            name = u.get('username') if isinstance(u, dict) else (getattr(u, 'username', None) or str(u))
        except Exception:
            name = str(u)
        if name and name not in seen:
            usernames.append(name)
            seen.add(name)
    # include the special 'all' selector
    if 'all' not in seen:
        usernames.append('all')
    usernames.remove('admin')
    return jsonify({'users': usernames})