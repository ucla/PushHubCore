"""
Copyright (c) 2013, Regents of the University of California
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

  * Redistributions of source code must retain the above copyright notice,
    this list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

  * Neither the name of the University of California nor the names of its
    contributors may be used to endorse or promote products derived from this
    software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

"""
This module provides mock classes for various interactions (mostly HTTP),
as well as access to fixture data as Python variables.
"""

from os.path import abspath, dirname, join
from requests.exceptions import HTTPError

path = abspath(dirname(__file__))

good_atom = open(join(path, 'fixtures', 'example.xml'), 'r').read()
updated_atom = open(join(path, 'fixtures', 'updated.xml'), 'r').read()
no_author_good_atom = open(
    join(path, 'fixtures', 'no-author-example.xml'), 'r').read()
no_author_updated_atom = open(
    join(path, 'fixtures', 'no-author-updated.xml'), 'r').read()


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
