import concurrent.futures
import http
import socket
import sys
import wsgiref.simple_server

class ThreadPoolServer(wsgiref.simple_server.WSGIServer):
    def __pre_init(self, max_threads):
        '''
        This must be called, by a deriving class, before __init__ is called.

        This is because the thread pool has to be set up before requests are
        processed, and because overriding __init__ is problematic while also
        changing its signature, *and* coöperating with IPv64Server.
        '''
        if sys.version_info.major <= 3 and sys.version_info.minor < 5:
            if max_threads is None:
                max_threads = 4
        self.__ex = concurrent.futures.ThreadPoolExecutor(max_threads)

    def process_request(self, request, client_address):
        self.__ex.submit(self.__process_request_thread, request, client_address)

    def __process_request_thread(self, request, client_address):
        '''
        Taken from socketserver.ThreadingMixIn
        '''
        try:
            self.finish_request(request, client_address)
            self.shutdown_request(request)
        except Exception:
            self.handle_error(request, client_address)
            self.shutdown_request(request)

    def server_close(self):
        super().server_close()
        self.__ex.shutdown()

class InstantShutdownServer(wsgiref.simple_server.WSGIServer):
    '''
    Connecting to the underlying SocketServer's listening socket will wake it
    up. It will then immediately check the shutdown flag, rather than waiting
    for the poll_interval.
    '''
    def shutdown(self):
        with socket.socket(self.socket.family) as s:
            s.setblocking(0)
            try:
                s.connect(self.socket.getsockname())
            except BlockingIOError:
                pass
            # Now the thread running serve_forever is waiting for the client
            # to send a request...
            super().shutdown()
        # Now our socket is closed, the thread running serve_forever will check
        # __shutdown_request and return.

class IPv64Server(wsgiref.simple_server.WSGIServer):
    def __pre_init(self, server_address, bind_v6only):
        '''
        This must be called, by a deriving class, before __init__ is called.

        This is because TCPServer.__init__ uses self.address_family to create
        the socket.
        '''
        self.address_family = socket.AF_INET6 if server_address.version == 6 else socket.AF_INET
        self.__bind_v6only = bind_v6only

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IP, 15, 1) # IP_FREEBIND
        if self.__bind_v6only is not None and self.address_family == socket.AF_INET6:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, self.__bind_v6only)
        super().server_bind()

class SilentRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    def log_request(self, code, message):
        if hasattr(http, 'HTTPStatus') and isinstance(code, http.HTTPStatus) and code.value < 400:
            return
        elif code[0] < '4':
            return
        super().log_request(code, message)

class Server(IPv64Server, InstantShutdownServer, ThreadPoolServer):
    '''
    A WSGIServer that works with IPv6, and processes requests concurrently.

    server_address[0] must be an ipaddress.ip_address, as opposed to the normal string.
    '''
    def __init__(self, server_address, RequestHandlerClass, max_threads, bind_v6only, bind_and_activate=True):
        self._IPv64Server__pre_init(server_address[0], bind_v6only)
        self._ThreadPoolServer__pre_init(max_threads)
        super().__init__((str(server_address[0]), server_address[1]), RequestHandlerClass, bind_and_activate)
