import socket
import selectors
import threading
import logging

import time
from logging import LogRecord

from GhostBot import logger as _logger
from GhostBot.IPC.message import Command, Message


class IPCServer:
    def __init__(self, host='localhost', port=64057, heartbeat_interval=5):
        self.logger = _logger.getChild(self.__class__.__name__)
        self.listening_thread = None
        self.host = host
        self.port = port
        self.heartbeat_interval = heartbeat_interval
        self.selector = selectors.DefaultSelector()
        self.clients = {}  # Stores {connection: last_activity_time}
        self.server_socket = None
        self.last_heartbeat_time = time.time()
        self.running = False

    def setup_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.server_socket.setblocking(False)
        self.selector.register(self.server_socket, selectors.EVENT_READ, self.accept)
        self.logger.info(f"Server listening on {self.host}:{self.port}...")
        self.running = True

    def accept(self, sock):
        conn, addr = sock.accept()
        self.logger.info(f"Accepted connection from {addr}")
        conn.setblocking(False)
        self.selector.register(conn, selectors.EVENT_READ, self.read)
        self.clients[conn] = time.time()

    def _dispatch(self, conn, data: str):
        """Override with your implementation"""
        print(conn, data)

    def read(self, conn):
        try:
            data = conn.recv(1024)
            if data:
                _data = data.decode('utf8')
                self.clients[conn] = time.time()
                try:
                    self._dispatch(conn, _data)
                except Exception as e:
                    self.logger.exception(e)
                return

            else:
                client_address = conn.getpeername()
                self.logger.info(f"Client {client_address} disconnected.")
        except ConnectionResetError:
            client_address = conn.getpeername()
            self.logger.error(f"Client {client_address} reset the connection.")
        except Exception as e:
            self.logger.error(f"Error reading from {conn.getpeername()}: {e}")
            self.logger.exception(e)
        self.remove_client(conn)

    def send_to_all(self, message):
        for client_conn in list(self.clients.keys()):  # Iterate over a copy
            self.send_to_client(client_conn, message)

    def send_to_client(self, conn, message):
        try:
            conn.sendall(message.encode('utf8'))
            return

        except OSError as e:
            self.logger.exception(e)
        except BrokenPipeError:
            client_address = conn.getpeername()
            self.logger.error(f"Client {client_address} is not available for sending.")
        except Exception as e:
            client_address = conn.getpeername()
            self.logger.error(f"Error sending to {client_address}: {e}")
            self.logger.exception(e)
        self.remove_client(conn)

    def remove_client(self, conn):
        if conn in self.clients:
            self.selector.unregister(conn)
            conn.close()
            del self.clients[conn]

    def send_heartbeats(self):
        current_time = time.time()
        if current_time - self.last_heartbeat_time >= self.heartbeat_interval:
            self.logger.debug("Sending heartbeats...")
            self.send_to_all(Command.SERVER_HEARTBEAT)
            self.last_heartbeat_time = current_time

    def start_listening_thread(self):
        self.listening_thread = threading.Thread(target=self._listening_thread_func, daemon=True)
        self.listening_thread.start()

    def _listening_thread_func(self):
        try:
            while self.running:
                # Use a timeout to allow periodic checks for heartbeats
                events = self.selector.select(timeout=1)

                if not events:
                    self.send_heartbeats()
                    continue

                for key, _ in events:
                    callback = key.data
                    callback(key.fileobj)
                time.sleep(0.05)
        except KeyboardInterrupt:
            self.logger.info("\nServer shutting down.")
        except Exception as e:
            self.logger.exception(e)
        finally:
            self.close_all_connections()

    def run(self):
        self.setup_server()
        time.sleep(1)
        self.start_listening_thread()

    def close_all_connections(self):
        self.running = False
        if self.server_socket:
            self.selector.unregister(self.server_socket)
            self.server_socket.close()
        for conn in list(self.clients.keys()):
            self.remove_client(conn)
        self.selector.close()
        self.logger.info("All connections closed.")


class IPCServerLogHandler(logging.Handler):
    def __init__(self, ipc_server: IPCServer):
        super().__init__()
        self._ipc_server = ipc_server

    def emit(self, record: LogRecord):
        log_entry = self.format(record)
        if record.levelno >= self._ipc_server.logger.level:
            self._ipc_server.send_to_all(Message(Command.LOG, target=log_entry))


if __name__ == "__main__":
    server = IPCServer(port=55555)
    server.run()
    while True:
        server.send_to_all(input('Message: '))
