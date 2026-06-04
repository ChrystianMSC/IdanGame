import socket
import threading

from src.network.NetworkEngine import NetworkEngine
from src.network.NetworkObserver import NetworkObserver
from src.network.NetworkProtocol import NetworkProtocol

class P2PNetworkManager(NetworkEngine):
    def __init__(self):
        self._observers = []
        self._server_socket = None
        self._connection_socket = None
        self._is_running = False

        self._receive_thread = None
        self._listen_thread = None

    def register_observer(self, observer):
        self._observers.append(observer)

    def start_as_host(self, host, port):
        self._is_running = True
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((host, port))
        self._server_socket.listen(1)

        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()

    def connect_as_guest(self, host, port):
        self._is_running = True
        self._connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._connection_socket.connect((host, port))
            self._start_receive_loop()
            return True
        except socket.error:
            self.disconnect()
            return False

    def _listen_loop(self):
        try:
            while self._is_running and self._server_socket:
                self._server_socket.settimeout(1.0)
                try:
                    conn, _ = self._server_socket.accept()
                    self._connection_socket = conn
                    self._start_receive_loop()
                    break
                except socket.timeout:
                    continue
        except Exception:
            if self._is_running:
                self._notify_connection_loss()

    def _start_receive_loop(self):
        self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._receive_thread.start()

    def _receive_loop(self):
        raw_buffer = ""
        while self._is_running and self._connection_socket:
            try:
                packet = self._connection_socket.recv(4096).decode('utf-8')
                if not packet:
                    raise ConnectionResetError()

                raw_buffer += packet
                payloads, raw_buffer = NetworkProtocol.parse_stream(raw_buffer)

                for payload in payloads:
                    self._notify_observers(payload)

            except (ConnectionResetError, socket.error):
                self._notify_connection_loss()
                break

    def send(self, data):
        if not self._connection_socket:
            return
        try:
            serialized_packet = NetworkProtocol.serialize(data)
            self._connection_socket.sendall(serialized_packet)
        except socket.error:
            self._notify_connection_loss()

    def disconnect(self):
        self._is_running = False
        if self._connection_socket:
            try:
                self._connection_socket.shutdown(socket.SHUT_RDWR)
                self._connection_socket.close()
            except socket.error:
                pass
        if self._server_socket:
            try:
                self._server_socket.close()
            except socket.error:
                pass

    def _notify_observers(self, data):
        for observer in self._observers:
            observer.on_message_received(data)

    def _notify_connection_loss(self):
        for observer in self._observers:
            observer.on_connection_lost()