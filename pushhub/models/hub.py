"""
Classes meant to represent the PubSubHubbub Hub.

The hub itself does not have state, but does hold references to
subscribers and topics.
"""

from zope.interface import Interface, implements


from repoze.folder import Folder


class IHub(Interface):
    """Marker interface for hub implementations"""
    pass


class Hub(Folder):
    implements(IHub)
    __name__ = __parent__ = None
    title = "Hub"

    def __init__(self):
        self.topics = None
        self.subscribers = None

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
