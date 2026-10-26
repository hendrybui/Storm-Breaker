"""P3.1 — auth blueprint.

Owns operator entry/exit: /login, /logout and the legacy .php aliases
that browsers and the panel JS still hit. The HTML shells for the
authenticated operator UI (/panel, /panel.php, /mobile_control) remain
in app.py for now -- they pull in load_check_c / change_token / token
helpers that fit a future admin_panel blueprint.

Migration source-of-truth: lines 191-258 of the legacy app.py. Code
in this module is verbatim from those lines except for moving
@app.route(...) decorators to @bp.route(...) and rewriting
url_for('panel') / url_for('login') to literal path redirects so this
blueprint doesn't depend on the future admin blueprint's endpoint name.

NR-2 note: routes keep their ORIGINAL Flask endpoint names (``login``,
``panel``, ``logout``, etc.) by passing ``endpoint="..."`` to the
decorator. The legacy ``flask_templates/login.html`` template uses
``url_for('login')`` to build the form action -- changing the endpoint
to ``auth.login`` would break that template until P11 (panel migration).
"""
from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session

from app.state import CONFIG, load_check_c


import time
bp = Blueprint("auth", __name__)


@bp.route('/', endpoint='index')
def index():
    key = load_check_c()
    cookie = request.cookies.get('logindata')
    if cookie and cookie == key.get('token') and key.get('expired') == 'no':
        return redirect('/panel')
    elif session.get('IAm-logined'):
        return redirect('/panel')
    else:
        return redirect('/login')


@bp.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    error = None
    if session.get('IAm-logined'):
        return redirect('/panel')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # config.php credentials (see app.state.CONFIG); loaded once at
        # import time of storm-web/app/state.py.
        if username in CONFIG and CONFIG[username]['password'] == password:
            session['IAm-logined'] = username
            return redirect('/panel')
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)


@bp.route('/login.php', methods=['GET', 'POST'], endpoint='login_php')
def login_php():
    return login()


@bp.route('/logout', endpoint='logout')
def logout():
    session.clear()
    resp = redirect('/login')
    resp.set_cookie('logindata', '', expires=0, path='/')
    return resp


@bp.route('/logout.php', endpoint='logout_php')
def logout_php():
    return logout()


@bp.route('/index.php', endpoint='index_php')
def index_php():
    return redirect('/login')

