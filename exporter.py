import argparse
import ipaddress
import socket
import urllib
import wsgiref

import prometheus_client

import igd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind-address', type=ipaddress.ip_address, default='::', help='IPv6 or IPv4 address to listen on')
    parser.add_argument('--bind-port', type=int, default=9196, help='Port to listen on')
    parser.add_argument('--bind-v6only', type=int, choices=[0, 1], help='If 1, prevent IPv6 sockets from accepting IPv4 connections; if 0, allow; if unspecified, use OS default')
    args = parser.parse_args()

    class IPv46Server(wsgiref.simple_server.WSGIServer):
        address_family = socket.AF_INET6 if args.bind_address.version == 6 else socket.AF_INET

        def server_bind(self):
            self.socket.setsockopt(socket.IPPROTO_IP, 15, 1) # IP_FREEBIND
            if args.bind_v6only is not None and args.bind_address.version == 6:
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, args.bind_v6only)
            super().server_bind()

    server = wsgiref.simple_server.make_server(str(args.bind_address), args.bind_port, wsgi_app, IPv46Server)
    server.serve_forever()

def wsgi_app(environ, start_response):
    name = wsgiref.util.shift_path_info(environ)
    if name == '':
        return front(environ, start_response)
    if name == 'probe':
        return probe(environ, start_response)
    elif name == 'metrics':
        return prometheus_app(environ, start_response)
    return not_found(environ, start_response)

def front(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [
        b'<html>'
            b'<head><title>WSG exporter</title></head>'
            b'<body>'
                b'<h1>WSG Exporter</h1>'
                b'<p><a href="/probe?target=http%3A%2F%2F192.0.2.1%2FRootDevice.xml">Probe http://192.0.2.1/RootDevice.xml</a>'
                b'<p><a href="/metrics">Metrics</a>'
            b'</body>'
        b'</html>'
    ]

def probe(environ, start_response):
    qs = urllib.parse.parse_qs(environ['QUERY_STRING'])
    body = igd.probe(qs['target'][0])
    start_response('200 OK', [('Content-Type', 'text/plain; charset=utf-8; version=0.0.4')])
    return body

prometheus_app = prometheus_client.make_wsgi_app()

def not_found(environ, start_response):
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return [b'Not Found\r\n']

if __name__ == '__main__':
    main()