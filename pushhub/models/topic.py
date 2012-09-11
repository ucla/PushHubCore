"""
A topic is a link published to the hub.

It has a last-updated timestamp, as well as the last-seen content for
generating diffs, so the hub knows what to send out to subscribers.
"""

from datetime import datetime
from urlparse import urlparse

from feedparser import parse
from persistent import Persistent
import requests
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
        self.subscribers = 0
        self.last_pinged = None
        self.ping()

    def fetch(self, hub_url):
        """Fetches the content from the publisher's provided URL"""

        user_agent = "PuSH Hub (+%s; %s)" % (hub_url, self.subscribers)

        headers = {'User-Agent': user_agent}

        response = requests.get(self.url, headers=headers)

        if not self.verify(response.content):
            raise ValueError
        self.content = response.content
        self.timestamp = datetime.now()

    def verify(self, content):
        """Verifies that the URL provides valid Atom/RSS responses."""
        parsed = parse(content)

        if parsed.bozo:
            return False
        else:
            return True

    def ping(self):
        """Registers the last time a publisher pinged the hub for this topic."""
        self.last_pinged = datetime.now()

    def add_subscriber(self):
        """Increment subscriber count so reporting on content fetch is easier.
        """
        self.subscribers += 1

    def remove_subscriber(self):
        """Sanely remove subscribers from the count
        """
        if self.subscribers <= 0:
            raise ValueError
        self.subscribers -= 1
