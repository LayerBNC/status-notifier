from flask import Flask, request
from datetime import datetime
import tweepy
import os

def create_app(debug=False):
    app = Flask(__name__)
    app.debug = debug

    return app

def setup_twitter():
    if not 'CONSUMER_KEY' in os.environ: raise KeyError('CONSUMER_KEY is not defined')
    if not 'CONSUMER_SECRET' in os.environ: raise KeyError('CONSUMER_SECRET is not defined')
    if not 'ACCESS_TOKEN' in os.environ: raise KeyError('ACCESS_TOKEN is not defined')
    if not 'ACCESS_SECRET' in os.environ: raise KeyError('ACCESS_SECRET is not defined')

    consumer_key = os.environ.get('CONSUMER_KEY')
    consumer_secret = os.environ.get('CONSUMER_SECRET')
    access_token = os.environ.get('ACCESS_TOKEN')
    access_secret = os.environ.get('ACCESS_SECRET')

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)

    return tweepy.API(auth)

app = create_app(False)
api = setup_twitter()
print('Logged in as @%s' % api.me().screen_name)

# This is the hook that goes into UptimeRobot
@app.route('/update', methods=['POST'])
def status_webhook():
    date_timestamp = request.json.get('alertDateTime')
    server_name = request.json.get('monitorFriendlyName')
    server_status = request.json.get('alertTypeFriendlyName')

    if server_name and server_status and date_timestamp:
        date_string = datetime.fromtimestamp(int(date_timestamp)).strftime("%b %d, %Y %X")
        server_status = server_status.lower()
        if server_status == 'down':
            message = '[down] Shortage registered for %s at %s. We are working to get the server back up ASAP. Apologies!' % (server_name, date_string)
        else:
            message = '[up] %s has resumed operation (%s), bouncers should reconnect shortly. Reach out to staff if you have any issue!' % (server_name, date_string)
        
        api.update_status(message)
    else:
        return 'ERROR', 400

    return 'OK'

@app.route('/')
def hello_world():
    return '<html><body><h1>It works!</h1></body></html>', 200

if __name__ == '__main__':
    if not 'OPENSHIFT_PYTHON_IP' in os.environ: ip = '127.0.0.1'
    else: ip = os.environ['OPENSHIFT_PYTHON_IP']

    app.run(host=ip, port=8080)