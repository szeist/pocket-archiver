import os
import time
from urllib.parse import quote
import requests
from flask import Flask, request, Response, redirect, session, jsonify
from flask_sslify import SSLify
from flask_httpauth import HTTPBasicAuth

SESSION_SECRET_KEY = os.environ['SESSION_SECRET_KEY']
POCKET_CONSUMER_KEY = os.environ['POCKET_CONSUMER_KEY']
POCKET_ACCESS_TOKEN = os.environ['POCKET_ACCESS_TOKEN']
AUTH_USER = os.environ['AUTH_USER']
AUTH_PASS = os.environ['AUTH_PASS']

app = Flask(__name__)
app.config['SECRET_KEY'] = SESSION_SECRET_KEY
sslify = SSLify(app, permanent=True)
auth = HTTPBasicAuth()

@auth.get_password
def get_pw(user):
    if user == AUTH_USER:
        return AUTH_PASS
    return None


@app.route('/get-access-token', methods=['GET'])
@auth.login_required
def get_access_token():
    session.pop('pocket_oauth_acces_code', None)
    redirect_uri = '%s://%s/show-access-token' % (request.scheme, request.host)
    data = {
        "consumer_key": POCKET_CONSUMER_KEY,
        "redirect_uri": redirect_uri
    }
    req = requests.post(
        'https://getpocket.com/v3/oauth/request',
        headers={ 'X-Accept': 'application/json' },
        json=data)
    if req.status_code != 200:
        error_body = 'OAuth error: [%s] %s' % (req.status_code, req.text)
        return Response(error_body, 500)
    response_json = req.json()
    oauth_code = response_json['code']
    session['pocket_oauth_access_code'] = oauth_code
    return redirect('https://getpocket.com/auth/authorize?request_token=%s&redirect_uri=%s' % (oauth_code, redirect_uri))


@app.route('/show-access-token', methods=['GET'])
@auth.login_required
def show_access_token():
    access_code = session.pop('pocket_oauth_access_code', None)
    if not access_code:
        return Response('No access code', 500)
    data = {
        'consumer_key': POCKET_CONSUMER_KEY,
        'code': access_code
    }
    req = requests.post(
        'https://getpocket.com/v3/oauth/authorize',
        headers={ 'X-Accept': 'application/json' },
        json=data)
    if req.status_code != 200:
        error_body = 'OAuth error: [%s] %s' % (req.status_code, req.text)
        return Response(error_body, 500)
    response_json = req.json()
    return 'Pocket user: %s<br>Access token: %s' % (response_json['username'], response_json['access_token'])


@app.route('/archive-old-articles', methods=['POST'])
@auth.login_required
def archive_old_articles():
    timestamp_to_keep = int(time.time()) - 7 * 24 * 3600
    data = {
        "consumer_key": POCKET_CONSUMER_KEY,
        "access_token": POCKET_ACCESS_TOKEN
    }
    req = requests.post(
        'https://getpocket.com/v3/get',
        headers={ 'X-Accept': 'application/json' },
        json=data
    )
    response_json = req.json()

    articles_to_archive = [article['item_id'] for article in response_json['list'].values() if int(article['time_added']) < timestamp_to_keep]

    if articles_to_archive:
        data = {
            "consumer_key": POCKET_CONSUMER_KEY,
            "access_token": POCKET_ACCESS_TOKEN,
            "actions": [{"action": "archive", "item_id": item_id} for item_id in articles_to_archive]
        }
        req = requests.post(
            'https://getpocket.com/v3/send',
            headers={ 'X-Accept': 'application/json' },
            json=data
        )
        if req.status_code != 200:
            return Response('Archive errror [%s]: %s' % (req.status_code, req.text), 500)

    return jsonify({"success": True})


if __name__ == '__main__':
    app.run()