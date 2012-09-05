"""
Classes that describe subscribers to the Hub's topics.

Subscribers have a list of topics they are subscribed to, and callback URL
that will be hit when any of those topics are updated.
"""

from persistent import Persistent
from repoze.folder import Folder
from zope.interface import Interface, implements


class Subscribers(Folder):
    """Folder to hold our subscribers"""
    title = "Subscribers"


class ISubscriber(Interface):
    """Marker interface for subscribers"""
    pass


class Subscriber(Persistent):
    implements(ISubscriber)

    def __init__(self, callback_url):
        self.callback_url = callback_url
        self.topics = Folder()
