# source: https://defn.io/2018/02/25/web-app-from-scratch-01/

import mimetypes
import os
import socket
from sys import path
import typing
from request import Request
from response import Response

SERVER_ROOT = os.path.abspath("www")

HOST = "127.0.0.1"
PORT = 9000

RESPONSE = b"""\
HTTP/1.1 200 OK
Content-type: text/html
Content-length: 15

<h1>Hello!</h1>""".replace(b"\n", b"\r\n")

FILE_RESPONSE_TEMPLATE = """\
HTTP/1.1 200 OK
Content-type: {content_type}
Content-length: {content_length}

""".replace("\n", "\r\n")

BAD_REQUEST_RESPONSE = b"""\
HTTP/1.1 400 Bad Request
Content-type: text/plain
Content-length: 11

Bad Request""".replace(b"\n", b"\r\n")

NOT_FOUND_RESPONSE = b"""\
HTTP/1.1 404 Not Found
Content-type: text/plain
Content-length: 9

Not Found""".replace(b"\n", b"\r\n")

METHOD_NOT_ALLOWED_RESPONSE = b"""\
HTTP/1.1 405 Method Not Allowed
Content-type: text/plain
Content-length: 17

Method Not Allowed""".replace(b"\n", b"\r\n")


def iter_lines(sock: socket.socket, bufsize: int = 16_384) -> typing.Generator[bytes, None, bytes]:
    """Given a socket, read all the individual CRLF-separated lines
    and yield each one until an empty one is found.  Returns the
    remainder after the empty line.
    """
    buff = b""
    while True:
        # Receive data from the socket. The return value is a bytes object representing the data received. 
        # The maximum amount of data to be received at once is specified by bufsize.
        # 
        # Note: For best match with hardware and network realities, the value of bufsize should be a relatively small power of 2, for example, 4096.
        data = sock.recv(bufsize)
        
        if not data:
            return b""
        
        buff += data
        while True:
            try:
                i = buff.index(b"\r\n")
                line, buff = buff[:i], buff[i + 2:]
                if not line:
                    return buff

                yield line
            except IndexError:
                break



def serve_file(sock: socket.socket, path: str) -> None:
    """Given a socket and the relative path to a file (relative to
    SERVER_SOCK), send that file to the socket if it exists.  If the
    file doesn't exist, send a "404 Not Found" response.
    """

    if path == "/":
        path = "/index.html"

    abspath = os.path.normpath(os.path.join(SERVER_ROOT, path.lstrip("/")))

    if not abspath.startswith(SERVER_ROOT):
        response = Response(status="404 NOT FOUND", content="Not Found")
        response.send(sock)
        return

    try:
        with open(abspath, "rb") as f:
            content_type, encoding = mimetypes.guess_type(abspath)
            """
                - MIME type:
                    more: https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types

                    A media type (also known as a Multipurpose Internet Mail Extensions or MIME type) 
                    is a standard that indicates the nature and format of a document, file, or assortment of bytes.

                    application/octet-stream is the default MIME type, representing arbitrary data, but it is recommeneded
                    to use more specific MIME type.
            """
            if content_type is None:
                content_type = "application/octet-stream"

            if encoding is not None:
                content_type += "; charset={}".format(encoding)

            response = Response(status="200 OK", body=f)
            response.headers.add("content-type", content_type)
            response.send(sock)
            return
    except FileNotFoundError:
        response = Response(status="404 NOT FOUND", content="Not Found")
        response.send(sock)
        return


with socket.socket() as server_sock:
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(0)
    print(f"Listening on {HOST}:{PORT}...")

    while True:
        client_sock, client_addr = server_sock.accept()
        print(f"Received connection from {client_addr}...")
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
                    continue

                serve_file(client_sock, request.path)
            except Exception as e:
                print(f"Failed to parse request: {e}")
                response = Response(status="400 Bad Request", content="Bad Request")
                response.send(client_sock)