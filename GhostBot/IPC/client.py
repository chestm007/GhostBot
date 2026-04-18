import socket
import selectors
import threading
import time
from traceback import print_exception

from GhostBot import logger as _logger
from GhostBot.lib.utils import retry
from GhostBot.rpc.message import Command


class IPCClient:
    def __init__(self, host='localhost', port=64057):
        self.logger = _logger.getChild(self.__class__.__name__)
        self.host = host
        self.port = port
        self.selector = selectors.DefaultSelector()
        self.client_socket = None
        self.running = True
        self.send_thread = None
        self.listening_thread = None

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
            self.client_socket.setblocking(False)
            self.logger.info("Connected to server at %s:%s", self.host, self.port)
            time.sleep(0.5)
            self.selector.register(self.client_socket, selectors.EVENT_READ, self.read)
            self.running = True
        except BlockingIOError:
            # Connection is in progress, will be completed later
            pass
        except ConnectionRefusedError:
            self.logger.error("Connection refused by server at %s:%s.", self.host, self.port)
            self.running = False
        except Exception as e:
            self.logger.error("Error connecting to server.")
            self.logger.exception(e)
            self.running = False

    def _dispatch(self, data: bytes):
        """Override with your implementation"""
        _data = data.decode('utf8')
        try:
            if Command.from_value(_data) == Command.SERVER_HEARTBEAT:
                self.logger.debug('received HEARTBEAT')
                return
        except ValueError:
            pass
        print(data)

    def read(self, sock):
        try:
            data = sock.recv(1024)
            if data:
                self.logger.debug("Received from server: %s", data)
                return self._dispatch(data)
            else:
                self.logger.info("Server closed the connection.")
                self.stop()
                return
        except ConnectionResetError:
            self.logger.error("Server reset the connection.")
            self.stop()
        except Exception as e:
            self.logger.error("Error reading from server.")
            self.logger.exception(e)

    def _reconnect(self):
        if not self.running:
            self.logger.debug("Client is not running, reconnecting...")
            self.run()
        return self.running

    def send_message(self, message):
        if not retry(self._reconnect, 5, 2):
            self.logger.error("Could not reconnect to server.")
            return
        try:
            if self.client_socket:
                self.client_socket.sendall(message.encode('utf8'))
                return
            self.logger.error("Error sending message, no self.client_socket available.")
            return
        except BrokenPipeError:
            self.logger.error("Could not send message. Server connection lost.")
            self.stop()
        except EOFError:
            self.logger.info("Exiting.")
            self.stop()
        except Exception as e:
            self.logger.error(f"Error sending message. {message}")
            self.logger.exception(e)
            self.stop()

    def start_listening_thread(self):
        self.listening_thread = threading.Thread(target=self._listening_thread_func, daemon=True)
        self.listening_thread.start()

    def _listening_thread_func(self):
        try:
            while self.running:
                # Use a timeout to allow the send_thread to run and check self.running
                events = self.selector.select(timeout=0.5)

                if not events:
                    continue

                for key, _ in events:
                    callback = key.data
                    callback(key.fileobj)
        except Exception as e:
            self.logger.exception(e)
            print_exception(e)
        finally:
            self.stop()

    def run(self):
        self.connect()
        if not self.running:
            return

        # self.start_sending_thread()
        time.sleep(0.5)
        self.start_listening_thread()

    def stop(self):
        self.logger.info("Client shutting down.")
        self.running = False
        if self.client_socket:
            try:
                self.selector.unregister(self.client_socket)
            except Exception as e:
                self.logger.error(e)
            self.client_socket.close()
        self.selector.close()
        self.logger.info("Client connection closed.")

if __name__ == "__main__":
    client = IPCClient(port=55555)
    client.run()
    while True:
        client.send_message(input("Message: "))
