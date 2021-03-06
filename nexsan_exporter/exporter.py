import io
import socket
import urllib
import wsgiref.util

import prometheus_client

from . import nexsan

def wsgi_app(environ, start_response):
    '''
    Base WSGI application that routes requests to other applications.
    '''
    name = wsgiref.util.shift_path_info(environ)
    if name == '':
        return front(environ, start_response)
    if name == 'probe':
        return probe(environ, start_response)
    elif name == 'metrics':
        return prometheus_app(environ, start_response)
    return not_found(environ, start_response)

def front(environ, start_response):
    '''
    Front page, containing a form for interactive use, and a link to the
    exporter's own metrics.
    '''
    with io.BytesIO() as page:
        page.write(
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

        start_response('200 OK', [('Content-Type', 'text/html')])
        return [page.getvalue()]

def probe(environ, start_response):
    '''
    Performs a probe using the given target address.
    '''
    qs = urllib.parse.parse_qs(environ['QUERY_STRING'])

    reg = prometheus_client.CollectorRegistry()
    reg.register(nexsan.probe(target=qs['target'][0], user=qs['user'][0], pass_=qs['pass'][0]))
    body = prometheus_client.generate_latest(reg)

    start_response('200 OK', [('Content-Type', prometheus_client.CONTENT_TYPE_LATEST)])
    return [body]

prometheus_app = prometheus_client.make_wsgi_app()

def not_found(environ, start_response):
    '''
    How did we get here?
    '''
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return [b'Not Found\r\n']
