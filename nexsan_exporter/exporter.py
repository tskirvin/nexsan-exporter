import io
import urllib

from flask import Flask, request
import prometheus_client
import werkzeug.wsgi

from . import nexsan

app = Flask(__name__)

@app.route('/')
def front():
    '''
    Front page, containing a form for interactive use, and a link to the
    exporter's own metrics.
    '''
    return (
        b'<html>'
            b'<head>'
                b'<title>Nexsan exporter</title>'
                b'<style>'
                    b'form { display: grid; grid-template-columns: 175px 175px; grid-gap: 16px; }'
                    b'label { grid-column: 1 / 2; text-align: right; }'
                    b'input, button { grid-column: 2 / 3; }'
                b'</style>'
            b'</head>'
            b'<body>'
                b'<h1>Nexsan Exporter</h1>'
                b'<p>Use this form to probe an array:'
                b'<form method="get" action="/probe">'
                    b'<label for="target">Probe address:</label>'
                    b'<input type="text" id="target" name="target" required placeholder="192.0.2.1">'
                    b'<label for="user">User:</label>'
                    b'<input type="text" id="user" name="user" required placeholder="admin">'
                    b'<label for="pass">Password:</label>'
                    b'<input type="password" required id="pass" name="pass">'
                    b'<button type="submit">Probe</button>'
                b'</form>'
                b'<hr>'
                b'<p><a href="/metrics">Metrics</a>'
            b'</body>'
        b'</html>'
    )

@app.route('/probe')
def probe():
    '''
    Performs a probe using the given target address.
    '''
    reg = prometheus_client.CollectorRegistry()
    reg.register(nexsan.probe(target=request.args.get('target'), user=request.args.get('user'), pass_=request.args.get('pass')))
    return Response(prometheus_client.generate_latest(reg), mimetype=prometheus_client.CONTENT_TYPE_LATEST)

application = werkzeug.wsgi.DispatcherMiddleware(app, {
    '/metrics': prometheus_client.make_wsgi_app()
})
