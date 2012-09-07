"""
A topic is a link published to the hub.

It has a last-updated timestamp, as well as the last-seen content for
generating diffs, so the hub knows what to send out to subscribers.
"""

from datetime import datetime
from urlparse import urlparse

from persistent import Persistent
from repoze.folder import Folder
from zope.interface import Interface, implements


class Topics(Folder):
    title = u"Topics"


class ITopic(Interface):
    """Marker interface for topics."""
    pass


class Topic(Persistent):
    implements(ITopic)

    def __init__(self, url):
        """Initialize the topic and it's timestamp/content.
        Verification happens afterward.
        """

        # Do some basic sanity checks

        pieces = urlparse(url)

        if not (pieces.scheme and pieces.netloc and pieces.path):
            raise ValueError

        self.url = url
        self.timestamp = None
        self.content = None
        self.last_pinged = None
        self.ping()

    def fetch(self):
        """Fetches the content from the publisher's provided URL"""
        pass
        # update timestamp
        # set self.content

    def verify(self):
        """Verifies that the URL provides valid Atom/RSS responses."""
        # Call inside of fetch? Perhaps before setting the content.
        pass

    def ping(self):
        """Registers the last time a publisher pinged the hub for this topic."""
        self.last_pinged = datetime.now()
