"""
This module provides mock classes for various interactions (mostly HTTP),
as well as access to fixture data as Python variables.
"""

from os.path import abspath, dirname, join

path = abspath(dirname(__file__))

good_atom = open(join(path, 'fixtures', 'example.xml'), 'r').read()


class MockResponse(object):
    """Mocks a response object, mostly for Requests.
    """
    def __init__(self, content=None, headers=None, status_code=None):
        self.content = content
        self.headers = headers
        self.status_code = status_code

    def __call__(self, *args, **kwargs):
        return self


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
