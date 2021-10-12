import socket
import typing
from request import Request
from response import Response
from HTTPWorker import HTTPWorker
from queue import Queue

class HTTPServer:
    def __init__(self, host="127.0.0.1", port=9000, worker_count=16) -> None:
        self.host = host
        self.port = port
        self.worker_count = worker_count
        self.worker_backlog = worker_count * 8
        self.connection_queue = Queue(self.worker_backlog)

    def serve_forever(self) -> None:
        workers = []
        for _ in range(self.worker_count):
            worker = HTTPWorker(self.connection_queue)
            worker.start()
            workers.append(worker)

        with socket.socket() as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.host, self.port))
            server_sock.listen(self.worker_backlog)
            print(f"Listening on {self.host}:{self.port}...")

            while True:
                try:
                    self.connection_queue.put(server_sock.accept())
                except KeyboardInterrupt:
                    break

        for worker in workers:
            worker.stop()

        for worker in workers:
            worker.join(timeout=30)



server = HTTPServer()
server.serve_forever()
