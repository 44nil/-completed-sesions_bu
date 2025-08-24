from flask import session as flask_session, redirect, url_for
from functools import wraps

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not flask_session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper
