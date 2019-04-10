#!/usr/bin/env python3
import os
import threading
import time

from flask import current_app, Flask, jsonify, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key',
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://localhost/mtmg-backend',
    SQLALCHEMY_TRACK_MODIFICATIONS = False
)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Enigma solution model
class Enigma(db.Model):
    __tablename__ = 'enigma'
    id = db.Column(db.Integer, primary_key=True)
    secret = db.Column(db.String(40), unique=True, nullable=False)
    target_url = db.Column(db.String(120), nullable=False)
    webhook_url = db.Column(db.String(120))
    discovery_count = db.Column(db.Integer, nullable=False, server_default='0', default=0)

    def __repr__(self):
        return '<Enigma %d>' % self.id


# Alert a webhook when someone solves an enigma
def enigma_alert(flask_app, url, secret, count, name):
    webhook_body = {
        'value1': str(secret),
        'value2': str(count),
        'value3': str(name)
    }
    response = requests.post(url, json=webhook_body)
    if response.status_code == 200:
        flask_app.logger.info('Webhook for enigma "{}" count "{}" was successful.'.format(secret, count))
    else:
        flask_app.logger.error('Webhook for enigma "{}" count "{}" failed: {}'.format(secret, count, response.reason))


# Try to guess the enigma
@app.route('/enigma', methods=['POST'])
def enigma():
    response_dict = {'status': 'error', 'reason': 'Segredo incorreto! Tente novamente...'}
    name = request.form.get('name', None)
    if not name:
        response_dict['reason'] = 'Você deve informar o seu nome.'
        return jsonify(response_dict)
    secret = request.form.get('secret', None)
    if not secret:
        response_dict['reason'] = 'Você deve enviar a tentativa de segredo.'
        return jsonify(response_dict)
    enigma = Enigma.query.filter_by(secret=secret).first()
    if enigma:
        if enigma.webhook_url:
            # Asynchronously notify by webhook
            url = enigma.webhook_url
            secret = enigma.secret
            name = request.form.get('name') or 'Pessoa Desconhecida'
            count = enigma.discovery_count + 1
            thread = threading.Thread(target=enigma_alert, \
                args=(current_app._get_current_object(), url, secret, count, name))
            thread.start()
        enigma.discovery_count += 1
        db.session.commit()
        response_dict['reason'] = 'Você descobriu o enigma! Aguarde para ser redirecionado...'
        response_dict['status'] = 'success'
        response_dict['url'] = enigma.target_url
    return jsonify(response_dict)


if __name__ == '__main__':
    app.debug = bool(os.environ.get('DEBUG_MODE'))
    app.run()
