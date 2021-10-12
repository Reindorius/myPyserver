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