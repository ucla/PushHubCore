"""
Classes meant to represent the PubSubHubbub Hub.

The hub itself does not have state, but does hold references to
subscribers and topics.
"""

from zope.interface import Interface, implements


from repoze.folder import Folder


from .topic import Topics, Topic


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

    def publish(self, topic_url):
        """
        Publish a topic to the hub.
        """
        if not self.topics:
            self.topics = Topics()

        topic = self.topics.get(topic_url, None)

        if not topic:
            topic = Topic(topic_url)
            self.topics.add(topic_url, topic)

        topic.ping()


    def notify_subscribers(self):
        """
        Sends updates to each of the subscribers to let them know
        of new topic content.
        """
        pass
