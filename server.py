# source: https://defn.io/2018/02/25/web-app-from-scratch-01/

import socket
import typing

HOST = "127.0.0.1"
PORT = 9000

RESPONSE = b"""\
HTTP/1.1 200 OK
Content-type: text/html
Content-length: 15

<h1>Hello!</h1>""".replace(b"\n", b"\r\n")

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


class Request(typing.NamedTuple):
    method: str
    path: str
    headers: typing.Mapping[str, str]


with socket.socket() as server_sock:
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(0)
    print(f"Listening on {HOST}:{PORT}...")

    while(True):
        client_sock, client_addr = server_sock.accept()
        print("New connection from {}".format({client_addr}))
        with client_sock:
            for request_line in iter_lines(client_sock):
                print(request_line)

            client_sock.sendall(RESPONSE)