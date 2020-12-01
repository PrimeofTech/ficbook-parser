import hashlib
from functools import wraps
from flask import Flask, g, request, make_response, render_template, redirect, url_for
from os import path
from datetime import datetime
from json import dumps
import shelve
import time
import random

from parsers import Parser

basedir = path.abspath(path.dirname(__file__))
SESSION_LENGTH = 30 * 60  # seconds

app = Flask(__name__)
app.config['SECRET_KEY'] = 'A super duper badass hard to guess key'  # TODO: get this from env


def get_random_string(length=64, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    random.seed(
        hashlib.sha256(
            ("%s%s%s" % (
                random.getstate(),
                time.time(),
                app.config['SECRET_KEY'])).encode('utf-8')
        ).digest())
    return ''.join(random.choice(allowed_chars) for _ in range(length))


def haskey(dict_obj, key, checkempty=False):
    if key in dict_obj.keys():
        if checkempty and dict_obj[key] == '':
            return False
        return True
    else:
        return False


def session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if haskey(request.cookies, 'SESSID', checkempty=True):
            sid = request.cookies['SESSID']
            with shelve.open('data/sessions', 'c') as db:
                if haskey(db, sid) and haskey(db[sid], 'exp') and db[sid]['exp'] > int(time.time()):
                    sess = db[sid]
                    g.id = sid
                    g.session = sess
                    return f(*args, **kwargs)
                else:
                    response = make_response(redirect(url_for('index')))
                    response.set_cookie('SESSID', '')
                    return response
        else:
            response = make_response(redirect(url_for('index', next=request.path)))
            response.set_cookie('SESSID', '')
            return response
    return decorated_function


def redirect_dest(fallback):
    dest = request.args.get('next')
    print(dest)
    try:
        dest_url = url_for(dest)
    except Exception:
        return redirect(fallback)
    return redirect(dest_url)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':

        # TEMPORARY!!!
        response = make_response(render_template('index.html'))
        response.set_cookie('SESSID', '')
        return response

        if haskey(request.cookies, 'SESSID', checkempty=True):
            return 'existing sessid, <a href="/run">continue?</a>'
        return render_template('index.html')
    elif request.method == 'POST':
        sid = get_random_string()
        now = int(time.time())
        sess = {
            'iss': 'test-srv-1', 'sub': 'session', 'aud': 'filtered',  # statics
            'exp': now + SESSION_LENGTH,
            'iat': now,
            'ip': request.remote_addr,
            'status': 'created'
        }
        with shelve.open('data/sessions', 'c') as database:
            database[sid] = sess
        response = make_response(redirect(url_for('run')))
        response.set_cookie('SESSID', sid, max_age=SESSION_LENGTH,
                            # secure=True
                            )
        return response


@app.route('/run', methods=['GET', 'POST'])
@session_required
def run():
    stats = f"You are authorized with SESSID: {g.id} " \
           f"which was initialized at {datetime.fromtimestamp(g.session['iat'])} " \
           f"and expires at {datetime.fromtimestamp(g.session['exp'])}."
    response = make_response(render_template('gui.html', stats=stats))
    return response


@app.route('/login', methods=['post'])
@session_required
def login():
    if not haskey(request.json, 'uname') or not haskey(request.json, 'upswd'):
        return dumps({'OK': False}), 400
    uname = request.json['uname']
    upswd = request.json['upswd']
    with shelve.open('data/sessions', 'c', writeback=True) as database:
        database[g.id]['uname'] = uname
        database[g.id]['upswd'] = upswd
        database[g.id]['status'] = 'launched'
    Parser(g.id, uname, upswd, headless=True, verbose=True).start()
    return dumps({'OK': True})


@app.route('/status')
@session_required
def status():
    try:
        with shelve.open('data/sessions', 'c') as database:
            return dumps({'status': database[g.id]['status']})
    except KeyError:
        return dumps({'OK': False}), 500


@app.route('/result')
@session_required
def result():
    try:
        with shelve.open('data/sessions', 'c') as database:
            if not haskey(database, g.id):
                return dumps({'OK': False}), 404
            if database[g.id]['status'] != 'parser:extraction_successful':
                return dumps({'OK': True, 'data': {}})
            return dumps({'OK': True, 'data': database[g.id]['data']})
    except KeyError:
        return dumps({'OK': False}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)