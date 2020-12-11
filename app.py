import hashlib
from functools import wraps
from flask import Flask, request, make_response, render_template, redirect, url_for
from os import path
from datetime import datetime
from json import dumps
from tinydb import TinyDB, Query
import time
import random

from parsers import Parser
from database import Sessions

basedir = path.abspath(path.dirname(__file__))
SESSION_LENGTH = 60 * 60  # 60 minutes in seconds

app = Flask(__name__)
app.config['SECRET_KEY'] = 'A super duper badass hard to guess key'
Sessions = Sessions()


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
            sess = Sessions[sid]
            if sess and sess['exp'] <= int(time.time()):
                response = make_response(redirect(url_for('index')))
                response.set_cookie('SESSID', '')
                return response
            request.id = sid
            request.session = sess
            return f(*args, **kwargs)
        else:
            response = make_response(redirect(url_for('index')))
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
            'id': sid,
            'iss': 'test-srv-1', 'sub': 'session', 'aud': 'filtered',  # statics
            'exp': now + SESSION_LENGTH,
            'iat': now,
            'ip': request.remote_addr,
            'status': 'launched'
        }
        Sessions[sid] = sess
        response = make_response(redirect(url_for('run')))
        response.set_cookie('SESSID', sid, max_age=SESSION_LENGTH,
                            # secure=True
                            )
        return response


@app.route('/run', methods=['GET', 'POST'])
@session_required
def run():
    stats = f"You are authorized with SESSID: {request.id} " \
           f"which was initialized at {datetime.fromtimestamp(request.session['iat'])} " \
           f"and expires at {datetime.fromtimestamp(request.session['exp'])}."
    response = make_response(render_template('gui.html', stats=stats))
    return response


@app.route('/login', methods=['post'])
@session_required
def login():
    if not haskey(request.json, 'uname') or not haskey(request.json, 'upswd'):
        return dumps({'OK': False}), 400
    uname = request.json['uname']
    upswd = request.json['upswd']
    Sessions[request.id] = {
        'uname': uname,
        'status': 'launched'
    }
    Parser(request.id, uname, upswd, headless=True, verbose=True).start()
    return dumps({'OK': True})


@app.route('/status')
@session_required
def status():
    session = Sessions[request.id]
    if not session:
        return dumps({'OK': False}), 500
    return dumps({'status': session['status']})


@app.route('/result')
@session_required
def result():
    session = Sessions[request.id]
    if not session:
        return dumps({'OK': False}), 500
    if session['status'] != 'parser:extraction_successful':
        return dumps({'OK': True, 'data': {}})
    return dumps({'OK': True, 'data': session['data']})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
