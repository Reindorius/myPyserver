# source: https://defn.io/2018/02/25/web-app-from-scratch-01/

import mimetypes
import os
import socket
from sys import path
import typing
from request import Request

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


# class Request(typing.NamedTuple):
#     method: str
#     path: str
#     headers: typing.Mapping[str, str]

#     @classmethod
#     def from_socket(cls, sock: socket.socket) -> "Request":
#         """Read and parse the request from a socket object.

#         Raises:
#           ValueError: When the request cannot be parsed.
#         """

#         lines = iter_lines(sock)

#         try:
#             request_line = next(lines).decode("ascii")
#         except StopIteration:
#             raise ValueError("Request line missing")

#         try:
#             method, path, _ = request_line.split(" ")
#         except ValueError:
#             raise ValueError("Malformed request line {!r}".format(request_line))

#         headers = {}
#         for line in lines:
#             try:
#                 name, _, value = line.decode("ascii").partition(":")
#                 headers[name.lower()] = value.lstrip()
#             except ValueError:
#                 raise ValueError("Malformed request line {!r}".format(request_line))

#         return cls(method=method.upper(), path=path, headers=headers)


def serve_file(sock: socket.socket, path: str) -> None:
    """Given a socket and the relative path to a file (relative to
    SERVER_SOCK), send that file to the socket if it exists.  If the
    file doesn't exist, send a "404 Not Found" response.
    """

    if path == "/":
        path = "/index.html"

    abspath = os.path.normpath(os.path.join(SERVER_ROOT, path.lstrip("/")))

    if not abspath.startswith(SERVER_ROOT):
        sock.sendall(NOT_FOUND_RESPONSE)
        return

    try:
        with open(abspath, "rb") as f:
            stat = os.fstat(f.fileno())
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

            response_headers = FILE_RESPONSE_TEMPLATE.format(
                content_type = content_type,
                content_length = stat.st_size,
            ).encode("ascii")

            sock.sendall(response_headers)
            sock.sendfile(f)
    except FileNotFoundError:
        sock.sendall(NOT_FOUND_RESPONSE)
        return


with socket.socket() as server_sock:
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(0)
    print(f"Listening on {HOST}:{PORT}...")

    while(True):
        client_sock, client_addr = server_sock.accept()
        print("New connection from {}".format({client_addr}))
        with client_sock:
            try:
                request = Request.from_socket(client_sock)
                if "100-continue" in request.headers.get("expect", ""):
                    client_sock.sendall(b"HTTP/1.1 100 Continue\r\n\r\n")

                try:
                    content_length = int(request.headers.get("content-length","0"))
                except ValueError:
                    content_length = 0

                if content_length:
                    body = request.body.read(content_length)
                    print("Request Body", body)

                if request.method != "GET":
                    client_sock.sendall(METHOD_NOT_ALLOWED_RESPONSE)
                    continue

                serve_file(client_sock, request.path)
            except Exception as e:
                print("Failed to parse request: {}".format(e))
                client_sock.sendall(BAD_REQUEST_RESPONSE)