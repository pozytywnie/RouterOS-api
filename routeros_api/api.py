import hashlib
import binascii
from routeros_api import api_communicator
from routeros_api import communication_exception_parsers
from routeros_api import api_socket
from routeros_api import api_structure
from routeros_api import base_api
from routeros_api import exceptions
from routeros_api import resource


def connect(host, username='admin', password='', port=None, plaintext_login=False, use_ssl=False, ssl_verify=True, ssl_verify_hostname=True, ssl_context=None):
    return RouterOsApiPool(host, username, password, port, plaintext_login, use_ssl, ssl_verify, ssl_verify_hostname, ssl_context).get_api()


class RouterOsApiPool(object):
    socket_timeout = 15.0

    def __init__(self, host, username='admin', password='', port=None, plaintext_login=False, use_ssl=False, ssl_verify=True, ssl_verify_hostname=True, ssl_context=None):
        self.host = host

        if isinstance(username, bytes):
            username = username.decode()
        if isinstance(password, bytes):
            password = password.decode()

        self.username = username
        self.password = password

        self.plaintext_login = plaintext_login

        self.ssl_context = ssl_context
        # Use SSL? Ignored when using a context, so we will set it for simple reference when port-switching:
        if ssl_context is not None:
            self.use_ssl = True
        else:
            self.use_ssl = use_ssl
        self.ssl_verify = ssl_verify
        self.ssl_verify_hostname = ssl_verify_hostname

        self.port = port or self._select_default_port(self.use_ssl)

        self.connected = False
        self.socket = api_socket.DummySocket()
        self.communication_exception_parser = (
            communication_exception_parsers.ExceptionHandler())

    def get_api(self):
        if not self.connected:
            self.socket = api_socket.get_socket(self.host, self.port,
                                                timeout=self.socket_timeout, use_ssl=self.use_ssl, ssl_verify=self.ssl_verify, ssl_verify_hostname=self.ssl_verify_hostname, ssl_context=self.ssl_context)
            base = base_api.Connection(self.socket)
            communicator = api_communicator.ApiCommunicator(base)
            self.api = RouterOsApi(communicator)
            for handler in self._get_exception_handlers():
                communicator.add_exception_handler(handler)
            self.api.login(self.username, self.password, self.plaintext_login)
            self.connected = True
        return self.api

    def disconnect(self):
        self.connected = False
        self.socket.close()
        self.socket = api_socket.DummySocket()

    def set_timeout(self, socket_timeout):
        self.socket_timeout = socket_timeout
        self.socket.settimeout(socket_timeout)

    def _get_exception_handlers(self):
        yield CloseConnectionExceptionHandler(self)
        yield self.communication_exception_parser

    def _select_default_port(self, use_ssl):
        if use_ssl:
            return 8729
        else:
            return 8728


class RouterOsApi(object):
    def __init__(self, communicator):
        self.communicator = communicator

    def login(self, login, password, plaintext_login):
        if isinstance(login, str):
            login = login.encode()
        if isinstance(password, str):
            password = password.encode()

        response = None
        if plaintext_login:
            response = self.get_binary_resource('/').call('login',{ 'name': login, 'password': password })
        else:
            response = self.get_binary_resource('/').call('login')
        if 'ret' in response.done_message:
            token = binascii.unhexlify(response.done_message['ret'])
            hasher = hashlib.md5()
            hasher.update(b'\x00')
            hasher.update(password)
            hasher.update(token)
            hashed = b'00' + hasher.hexdigest().encode('ascii')
            self.get_binary_resource('/').call(
                'login', {'name': login, 'response': hashed})

    def get_resource(self, path, structure=None):
        structure = structure or api_structure.default_structure
        return resource.RouterOsResource(self.communicator, path, structure)

    def get_binary_resource(self, path):
        return resource.RouterOsBinaryResource(self.communicator, path)


class CloseConnectionExceptionHandler:
    def __init__(self, pool):
        self.pool = pool

    def handle(self, exception):
        connection_closed = isinstance(
            exception, exceptions.RouterOsApiConnectionError)
        fatal_error = isinstance(exception, exceptions.FatalRouterOsApiError)
        if connection_closed or fatal_error:
            self.pool.disconnect()
