"""
Classes meant to represent the PubSubHubbub Hub.

The hub itself does not have state, but does hold references to
subscribers and topics.
"""

from zope.component import provideUtility
from zope.interface import Interface, implements


from repoze.folder import Folder


class IHub(Interface):
    """Marker interface for hub implementations"""
    pass


class Hub(Folder):
    implements(IHub)
    __name__ = __parent__ = None

    def __init__(self, topics_folder, subscribers_folder):
        self.topics = topics_folder
        self.subscribers = subscribers_folder

    def publish(self):
        """
        Publish a topic to a particular feed
        """
        pass

    def notify_subscribers(self):
        """
        Sends updates to each of the subscribers to let them know
        of new topic content.
        """
        pass
