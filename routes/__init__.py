"""
Routes package initialization.
Blueprints are registered here and imported in app.py
"""

"""
Routes package initialization.
Each feature defines its own blueprint module; import them here so
the application can register them from `routes`.
"""

# Import individual blueprint objects from their modules so they are
# available as `routes.home_bp`, etc., to the app registration code.
from routes.auth_routes import auth_bp
from routes.home import home_bp
from routes.dashboard import dashboard_bp
from routes.study import study_bp
from routes.community import community_bp
from routes.challenges import challenges_bp
from routes.flashcards import flashcards_bp
from routes.progress import progress_bp
from routes.feed import feed_bp
from routes.friends import friends_bp
from routes.signup import signup_bp
from routes.profile import profile_bp
from routes.streak import streak_bp
from routes.timer import timer_bp

__all__ = [
	'auth_bp',
	'home_bp',
	'dashboard_bp',
	'study_bp',
	'community_bp',
	'challenges_bp',
	'flashcards_bp',
	'progress_bp',
	'feed_bp',
	'friends_bp',
	'signup_bp',
	'profile_bp',
	'streak_bp',
	'timer_bp',
]