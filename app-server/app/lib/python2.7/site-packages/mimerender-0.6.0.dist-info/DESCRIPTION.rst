This module provides a decorator that wraps a HTTP
request handler to select the correct render function for a given HTTP
Accept header. It uses mimeparse to parse the accept string and select the
best available representation. Supports Flask, Bottle, web.py and webapp2
out of the box, and it's easy to add support for other frameworks.

