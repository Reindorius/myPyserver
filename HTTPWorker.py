from threading import Thread
import socket
from request import Request
from response import Response
from server import serve_file
from queue import Empty, Queue
import typing


class HTTPWorker(Thread):
    def __init__(self, connection_queue: Queue) -> None:
        super().__init__(daemon=True)

        self.connection_queue = connection_queue
        self.running = False

    def stop(self) -> None:
        self.running = False

    def run(self) -> None:
        self.running = True
        while self.running:
            try:
                client_sock, client_addr = self.connection_queue.get(timeout=1)
            except Empty:
                continue

            try:
                self.handle_client(client_sock, client_addr)
            except Exception as e:
                print(f"Unhandled error: {e}")
                continue
            finally:
                self.connection_queue.task_done()

    def handle_client(self, client_sock: socket.socket, client_addr: typing.Tuple[str, int]) -> None:
        with client_sock:
            try:
                request = Request.from_socket(client_sock)
                if "100-continue" in request.headers.get("expect", ""):
                    response = Response(status="100 Continue")
                    response.send(client_sock)

                try:
                    content_length = int(request.headers.get("content-length", "0"))
                except ValueError:
                    content_length = 0

                if content_length:
                    body = request.body.read(content_length)
                    print("Request body", body)

                if request.method != "GET":
                    response = Response(status="405 Method Not Allowed", content="Method Not Allowed")
                    response.send(client_sock)
                    return

                serve_file(client_sock, request.path)
            except Exception as e:
                print(f"Failed to parse request: {e}")
                response = Response(status="400 Bad Request", content="Bad Request")
                response.send(client_sock)
