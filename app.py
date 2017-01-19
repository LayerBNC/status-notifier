#    This file is part of status-notifier.
#
#    status-notifier is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    status-notifier is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with status-notifier.  If not, see <http://www.gnu.org/licenses/>.
#
import os
from datetime import datetime, timedelta

from flask import Flask, request

import tweepy


server_downtimes = {}

def create_app(debug=False):
    app = Flask(__name__)
    app.debug = debug

    return app

def get_date_difference(a, b):
    now = datetime.utcfromtimestamp(a)
    other = datetime.utcfromtimestamp(b)

    dt = other - now
    total_s = dt.seconds + (dt.days * 60 * 60 * 24)
    if total_s:
        seconds = total_s % 60
        total_s /= 60
        minutes = int(total_s % 60)
        total_s /= 60
        hours = int(total_s % 24)
        total_s /= 24
        days = int(total_s)

    if days > 0:
        if hours > 0:
            if minutes > 0:
                return "%dd%02dh%02dm" % (days, hours, minutes)
            else:
                return "%dd%02dh" % (days, hours)
        else:
            return "%dd" % days
    if hours > 0:
        if minutes > 0:
            return "%dh%02dm" % (hours, minutes)
        else:
            return "%dh" % hours
    if minutes > 0:
        if seconds > 0:
            return "%dm%02ds" % (minutes, seconds)
        else:
            return "%dm" % minutes
    else:
        return "%02ds" % seconds

# Setup our Twitter account. If any of these
# tokens isn't defined, raise an error.
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

print('[%s] Status Notifier up and running' % datetime.utcnow().strftime("%x %X"))
app = create_app(False)
api = setup_twitter()
print('[%s] Logged in as @%s' % (datetime.utcnow().strftime("%x %X"), api.me().screen_name))

# This is the hook that goes into UptimeRobot
@app.route('/update', methods=['POST'])
def status_webhook():
    date_timestamp = request.json.get('alertDateTime')
    server_name = request.json.get('monitorFriendlyName')
    server_status = request.json.get('alertTypeFriendlyName')

    # Check if any of the required variables are defined.
    # If they aren't return HTTP 400
    if server_name and server_status and date_timestamp:
        # Get the current alert time from the timestamp
        # that is sent to us.
        date_string = datetime.utcfromtimestamp(int(date_timestamp)).strftime("%b %d, %Y %X")
        server_status = server_status.lower()

        if server_status == 'down':
            message = '[down] Shortage registered for %s at %s. We are working to get the server back up ASAP. Apologies!' % (server_name, date_string)
            server_downtimes[server_name] = int(date_timestamp)
        else:
            # Check if we have a downtime for the current server.
            # If we do, return the duration of downtime and
            # delete the entry from the dict.
            if server_name in server_downtimes:
                downtime_duration = get_date_difference(server_downtimes.get(server_name), int(date_timestamp))
                message = '[up] %s has resumed operation (%s, down for %s), bouncers should reconnect shortly.' % (server_name, date_string, downtime_duration)
                del server_downtimes[server_name]
            else:
                message = '[up] %s has resumed operation (%s), bouncers should reconnect shortly.' % (server_name, date_string)
        
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
