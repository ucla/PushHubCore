"""
A topic is a link published to the hub.

It has a last-updated timestamp, as well as the last-seen content for
generating diffs, so the hub knows what to send out to subscribers.
"""

from datetime import datetime

from persistent import Persistent
from repoze.folder import Folder


class Topics(Folder):
    title = u"Topics"


class Topic(Persistent):
    def __init__(self, url, timestamp, content):
        self.url = url
        self.timestamp = timestamp
        self.content = content
