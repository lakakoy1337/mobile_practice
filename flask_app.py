import random
import string
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storage.db'
db = SQLAlchemy(app)


def gen_token():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    secret = db.Column(db.String(30), nullable=False)


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account = db.Column(db.Integer, db.ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(10), default=gen_token, unique=True, nullable=False)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account = db.Column(db.Integer, db.ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(300), nullable=False)


def enable_fk(con, rec):
    con.execute('PRAGMA foreign_keys=ON')


with app.app_context():
    event.listen(db.engine, 'connect', enable_fk)
    db.create_all()


@app.route('/account', methods=['PUT'])
def manage_account():
    name = request.args.get('name')
    secret = request.args.get('secret')
    account = Account(name=name, secret=secret)
    db.session.add(account)
    try:
        db.session.commit()
        response_data = {
            'status': 'ok',
            'msg': 'Account created successfully',
            'id': account.id
        }
        return jsonify(response_data), 200
    except:
        db.session.rollback()
        response_data = {
            'status': 'error',
            'msg': 'Account already exists'
        }
        return jsonify(response_data), 200


@app.route('/session', methods=['PUT', 'DELETE'])
def manage_session():
    if request.method == 'PUT':
        name = request.args.get('name')
        secret = request.args.get('secret')
        account = Account.query.filter_by(name=name, secret=secret).first()
        if account is None:
            response_data = {
                'status': 'error',
                'msg': 'Invalid credentials'
            }
            return jsonify(response_data), 200

        session = Session(account=account.id)
        db.session.add(session)
        db.session.commit()
        response_data = {
            'status': 'ok',
            'msg': 'Session created successfully',
            'token': session.token
        }
        return jsonify(response_data), 200

    if request.method == 'DELETE':
        token = request.args.get('token')
        session = Session.query.filter_by(token=token).first()
        if session is None:
            response_data = {
                'status': 'error',
                'msg': 'Invalid token'
            }
            return jsonify(response_data), 200

        db.session.delete(session)
        db.session.commit()
        response_data = {
            'status': 'ok',
            'msg': 'Session deleted successfully'
        }
        return jsonify(response_data), 200


@app.route('/note', methods=['GET', 'PUT', 'POST', 'DELETE'])
def manage_note():
    id = request.args.get('id')
    token = request.args.get('token')
    session = Session.query.filter_by(token=token).first()
    if session is None:
        response_data = {
            'status': 'error',
            'msg': 'Invalid token'
        }
        return jsonify(response_data), 200

    if request.method == 'GET' and id is None:
        notes = Note.query.filter_by(account=session.account).all()
        note_list = []
        for note in notes:
            note_data = {
                'id': note.id,
                'title': note.title
            }
            note_list.append(note_data)
        response_data = {
            'status': 'ok',
            'msg': 'Notes retrieved successfully',
            'notes': note_list
        }
        return jsonify(response_data), 200

    title = request.args.get('title')
    content = request.args.get('content')

    if request.method == 'PUT':
        note = Note(account=session.account, title=title, content=content)
        db.session.add(note)
        db.session.commit()
        response_data = {
            'status': 'ok',
            'msg': 'Note created successfully'
        }
        return jsonify(response_data), 200

    else:
        note = Note.query.filter_by(account=session.account, id=id).first()
        if note is None:
            response_data = {
                'status': 'error',
                'msg': 'Note not found'
            }
            return jsonify(response_data), 200

        if request.method == 'POST':
            note.title = title
            note.content = content
            db.session.commit()
            response_data = {
                'status': 'ok',
                'msg': 'Note updated successfully'
            }
            return jsonify(response_data), 200

        if request.method == 'DELETE':
            db.session.delete(note)
            db.session.commit()
            response_data = {
                'status': 'ok',
                'msg': 'Note deleted successfully'
            }
            return jsonify(response_data), 200

    if request.method == 'GET':
        response_data = {
            'status': 'ok',
            'msg': 'Note retrieved successfully',
            'content': note.content
        }
        return jsonify(response_data), 200
