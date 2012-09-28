"""
This module provides mock classes for various interactions (mostly HTTP),
as well as access to fixture data as Python variables.
"""

from os.path import abspath, dirname, join
from requests.exceptions import HTTPError

path = abspath(dirname(__file__))

good_atom = open(join(path, 'fixtures', 'example.xml'), 'r').read()
updated_atom = open(join(path, 'fixtures', 'updated.xml'), 'r').read()


class MockResponse(object):
    """Mocks a response object, mostly for Requests.
    """
    def __init__(self, content=None, headers=None, status_code=None):
        self.content = content
        self.headers = headers
        self.status_code = status_code

    def __call__(self, *args, **kwargs):
        return self

    def raise_for_status(self):
        """Generates exceptions if HTTP status code isn't in 2xx range.

        Mocks the same method on requests's Response class, but does not
        set the error messages based on the code.
        """
        if self.status_code >= 300:
            raise HTTPError



class MultiResponse(object):
    """Maps URLs to objects.

    Useful when making several Requests calls in a row, each needing different
    criteria.
    """
    def __init__(self, mapping):
        self.mapping = mapping

    def __call__(self, url, *args, **kwargs):
        if url in self.mapping.keys():
            return self.mapping[url]
        else:
            return MockResponse(status_code=404)
