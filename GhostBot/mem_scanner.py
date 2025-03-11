import threading

import pymem

from GhostBot import logger
from GhostBot.client_window import ClientWindow


class BotController:
    def __init__(self):
        self.threads: dict[str, threading.Thread] = dict()
        self.clients: dict[str, ClientWindow] = dict()
        for proc in pymem.process.list_processes():
            if proc.szExeFile == b'client.exe':
                client = ClientWindow(proc)
                self.add_client(client)

    @property
    def client_keys(self):
        return list(str(k) for k in self.clients.keys())

    def add_client(self, client: ClientWindow) -> None:
        self.threads[client.name] = threading.Thread(target=self._run_scan, args=(client, ))
        self.clients[client.name] = client

    def start_bot(self, client: ClientWindow) -> None:
        self.threads.get(client.name).start()

    def _run_scan(self) -> None:
        pass

    def stop_all_bots(self, timeout=30) -> None:
        for client in self.clients.values():
            self.stop_bot(client, timeout)

    def stop_bot(self, client, timeout=30) -> None:
        for name, thread in self.threads.items():
            logger.info(f'stopping {client.name}')
            thread.join(timeout)


if __name__ == "__main__":
    c = BotController()
    c.start_scan()