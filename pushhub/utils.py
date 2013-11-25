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
Various utility functions.
"""
from copy import deepcopy
import urllib
import urlparse

from functools import wraps

from pyramid.httpexceptions import exception_response
from webhelpers.feedgenerator import Atom1Feed

import logging
logger = logging.getLogger(__name__)


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
    split = urlparse.urlparse(url)
    if not split.scheme in ('http', 'https'):
        return False

    netloc, port = (split.netloc.split(':', 1) + [''])[:2]

    if not netloc:
        return False

    if split.fragment:
        return False

    return True


class FeedComparator(object):
    def __init__(self, new_feed, past_feed):
        """
        Provides methods for comparing 2 Atom/RSS feeds.

        Arguments:
            * new_feed: The parsed feed of the newer content
            * past_feed: The parsed feed of an older version of the content.
        """
        self.new_feed = new_feed
        self.past_feed = past_feed

    def new_entries(self):
        """
        Finds new entries in the feed and returns them.

        New entries are determined by comparing the set of IDs
        found in each feed.
        """
        new = []
        new_entry_ids = [e.id for e in self.new_feed.entries]
        past_entry_ids = [e.id for e in self.past_feed.entries]

        for entry in self.new_feed.entries:
            if entry.id in new_entry_ids and entry.id not in past_entry_ids:
                new.append(entry)

        return new

    def updated_entries(self):
        """
        Finds existing updated entries and returns them.

        Entries are differentiated by their ID, and are considered updated
        if the parsed date/time of the new entry is more recent than the
        old entry's.
        """

        updated = []
        past_ids = [e.id for e in self.past_feed.entries]
        for entry in self.new_feed.entries:
            if entry.id not in past_ids:
                continue

            idx = past_ids.index(entry.id)
            past_entry = self.past_feed.entries[idx]
            if entry.updated_parsed > past_entry.updated_parsed:
                updated.append(entry)
            if entry.link != past_entry.link:
                updated.append(entry)
        return updated

    def removed_entries(self):
        removed = []
        new_ids = [e.id for e in self.new_feed.entries]
        for entry in self.past_feed.entries:
            if entry.id in new_ids:
                continue

            removed.append(entry)
        return removed

    def changed_metadata(self):
        """
        Detects changes to the feed metadata.

        If *any* of the attributes have changed, we use them all.
        """
        changed = False

        past_feed = self.past_feed['feed']
        new_feed = self.new_feed['feed']

        if past_feed['title'] != new_feed['title']:
            changed = True

        if past_feed.get('author', None) != new_feed.get('author', None):
            changed = True

        if len(new_feed.keys()) > len(past_feed.keys()):
            changed = True

        if changed:
            metadata = deepcopy(self.new_feed)
        else:
            metadata = deepcopy(self.past_feed)

        del metadata['entries']
        return metadata


class Atom1FeedKwargs(Atom1Feed):
    """An Atom1Feed that can handle the kwargs passed in for new feed
    items.

    XXX: This is far from optimal. Need to find a better solution for
         this problem.
    """

    # List of fields that have already been handled, or are generated
    default_fields = [
        'author_email',
        'author_link',
        'author_name',
        'categories',
        'description',
        'enclosure',
        'guidislink',
        'item_copyright',
        'link',
        'pubdate',
        'published',
        'published_parsed',
        'summary',
        'title',
        'ttl',
        'unique_id',
        'updated',
        'updated_parsed',
    ]

    def _handle_kwarg(self, handler, key, value):
        """Handle each item and recursively handle lists
        """
        if key in self.default_fields or value is None:
            logger.debug('ignoring: %s, %s' % (key, value))
            return
        if isinstance(value, dict):
            # Handle a dictionary and assume the "value" is what
            # will be the text of the element.
            value = deepcopy(value)
            el_content = value.pop('value', '')
            # The xml parser can't handle a None value
            for k, v in value.items():
                if v is None:
                    value.pop(k)
            if value.get("type") == "application/xhtml+xml": # XXX: fragile
                self.add_xml_element(handler, key, el_content, value)
            else:
                handler.addQuickElement(key, el_content, value)
        elif isinstance(value, (list, tuple)):
            # Loop over a list and add each item
            for item in value:
                self._handle_kwarg(handler, key, item)
        else:
            # Assume everything else is just a simple string
            handler.addQuickElement(key, value)

    def add_item_elements(self, handler, item):
        """Process all the default items, then try and add the elements
        from the keyword arguments.
        """
        super(Atom1FeedKwargs, self).add_item_elements(handler, item)
        for k, v in item.items():
            self._handle_kwarg(handler, k, v)

    def add_xml_element(self, handler, name, value, attrs):
        """Add element with XML content"""
        if attrs is None:
            attrs = {}
        handler.startElement(name, attrs)
        if value is not None:
            handler._write(value) # XXX: private access
        handler.endElement(name)
