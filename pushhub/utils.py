"""
Various utility functions.
"""
import urllib
import urlparse

from functools import wraps

from pyramid.httpexceptions import exception_response


def require_post(fn):
    """Requires that a function receives a POST request,
       otherwise returning a 405 Method Not Allowed.

       Requires that a function recieves a Content-type
       of application/x-www-form-urlencoded otherwise returning
       a 406 Not Acceptable.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # We could be called with (context, request) or just (request,)
        request = args[0]
        if len(args) > 1:
            request = args[1]
        if request.method != "POST":
            response = exception_response(405)
            response.headers.extend([('Allow', 'POST')])
            return response

        content_type = request.headers.get('Content-Type', None)
        if (content_type != "application/x-www-form-urlencoded"):
            response = exception_response(406)
            response.headers.extend(
                [('Accept', 'application/x-www-form-urlencoded')]
            )
            return response

        return fn(*args, **kwargs)
    return wrapper


# taken from the pubsubhubbub source
def normalize_iri(url):
    """Converts a URL (possibly containing unicode characters) to an IRI.

    Args:
    url: String (normal or unicode) containing a URL, presumably having
      already been percent-decoded by a web framework receiving request
      parameters in a POST body or GET request's URL.

    Returns:
    A properly encoded IRI (see RFC 3987).
    """
    def chr_or_escape(unicode_char):
        if ord(unicode_char) > 0x7f:
            return urllib.quote(unicode_char.encode('utf-8'))
        else:
            return unicode_char
    return ''.join(chr_or_escape(c) for c in unicode(url))


# taken from the pubsubhubbub source
def is_valid_url(url):
    """Returns True if the URL is valid, False otherwise."""
    from .views import VALID_PORTS
    split = urlparse.urlparse(url)
    if not split.scheme in ('http', 'https'):
        return False

    netloc, port = (split.netloc.split(':', 1) + [''])[:2]
    if port and port not in VALID_PORTS:
        return False

    if split.fragment:
        return False

    return True
