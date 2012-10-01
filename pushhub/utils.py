"""
Various utility functions.
"""
from copy import deepcopy
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

        if changed:
            new_metadata = deepcopy(self.new_feed)
            # Get rid of the entries so we can rebuild it.
            del new_metadata['entries']
            return new_metadata

        return None

