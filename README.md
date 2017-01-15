# status-notifier
Flask app that posts to Twitter whenever a server status changes.

It was created specially for LayerBNC, and was designed to be deployed on OpenShift, but the code can easily be adapted to your needs.

## How it works
It hosts a small Flask app that has a route for receiving payloads. In the case of LayerBNC, we receive an alert from UptimeRobot (we've setup a webhook alert contact) as JSON and post to Twitter when the status of a server changes.

You can fork and adapt the code to suit your needs, it shouldn't be that hard to do. If you need any help in doing it, feel free to send me an email at **alex [at] layerbnc [dot] org**.

## Install
There's no secret in installing status-notifier. You just need Python 3 to run the program.  
`pip install -r requirements.txt`