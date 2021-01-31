import hashlib
from functools import wraps
from flask import Flask, request, make_response, render_template, redirect, url_for
from os import path, getenv
from json import dumps
import time
import random

from parsers import Parser
from database import Sessions

basedir = path.abspath(path.dirname(__file__))
SERVER_NAME = getenv('SERVER_NAME', 'test-srv-1')
SESSION_LENGTH = int(getenv('SESSION_LENGTH', 60 * 60))  # 60 minutes in seconds
ENVIRONMENT = getenv('ENVIRONMENT', 'development')

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = getenv('SECRET_KEY')
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


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        if haskey(request.cookies, 'SESSID', checkempty=True):
            return redirect('/run')
        if 'ru' in request.headers['Accept-Language']:
            response = make_response(render_template('index.ru.html'))
        else:
            response = make_response(render_template('index.html'))
        return response
    elif request.method == 'POST':
        sid = get_random_string()
        now = int(time.time())
        sess = {
            'id': sid,
            'iss': SERVER_NAME, 'sub': 'session', 'aud': 'filtered',  # statics
            'exp': now + SESSION_LENGTH,
            'iat': now,
            'ip': request.remote_addr,
            'status': 'launched'
        }
        Sessions[sid] = sess
        response = make_response(redirect(url_for('run')))
        response.set_cookie('SESSID', sid, max_age=SESSION_LENGTH,
                            secure=(True if getenv('ENVIRONMENT', 'development') == 'production' else False))
        return response


@app.route('/clear-session')
def clear_session():
    response = make_response(redirect(url_for('index')))
    response.set_cookie('SESSID', '')
    return response


@app.route('/run', methods=['GET', 'POST'])
@session_required
def run():
    if 'ru' in request.headers['Accept-Language']:
        response = make_response(render_template('gui.ru.html'))
    else:
        response = make_response(render_template('gui.html'))
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
    Parser(request.id, uname, upswd, headless=(True if getenv('ENVIRONMENT', 'development') == 'production' else False),
           verbose=(False if getenv('ENVIRONMENT', 'development') == 'production' else True)).start()
    return dumps({'OK': True})


@app.route('/status')
@session_required
def status():
    session = Sessions[request.id]
    if not session:
        return dumps({'OK': False}), 500
    return dumps({'OK': True, 'status': session['status']})


@app.route('/result')
@session_required
def result():
    session = Sessions[request.id]
    try:
        return dumps({'OK': True, 'data': session['data']})
    except:
        return dumps({'OK': False})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=(False if getenv('ENVIRONMENT', 'development') == 'production' else True))
