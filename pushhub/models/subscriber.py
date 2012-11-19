"""
Classes that describe subscribers to the Hub's topics.

Subscribers have a list of topics they are subscribed to, and callback URL
that will be hit when any of those topics are updated.
"""
from datetime import datetime

from persistent import Persistent
from repoze.folder import Folder
from zope.interface import Interface, implements

from pushhub.utils import is_valid_url
from .topic import Topics


class Subscribers(Folder):
    """Folder to hold our subscribers"""
    title = "Subscribers"


class ISubscriber(Interface):
    """Marker interface for subscribers"""
    pass


class Subscriber(Persistent):
    implements(ISubscriber)

    def __repr__(self):
        return "<Subscriber '%s'>" % self.callback_url

    def __init__(self, callback_url):
        if not is_valid_url(callback_url):
            raise ValueError
        self.callback_url = callback_url
        self.topics = Topics()
        self.created_date = datetime.now()
