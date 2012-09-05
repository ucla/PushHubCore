"""
Various utility functions.
"""
from functools import wraps

from pyramid.httpexceptions import exception_response

from .models import appmaker
from pyramid_zodbconn import get_connection


def root_factory(request):
    conn = get_connection(request)
    return appmaker(conn.root())


def require_post(fn):
    """Requires that a function receives a POST request,
       otherwise returning a 405 Method Not Allowed.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        request = args[0]
        if request.method != "POST":
            response = exception_response(405)
            response.headers.extend([('Allow', 'POST')])
            return response

        return fn(*args, **kwargs)
    return wrapper
