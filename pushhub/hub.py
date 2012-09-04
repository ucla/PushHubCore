"""
Classes meant to represent the PubSubHubbub Hub.

The hub itself does not have state, but does hold references to
subscribers and topics.
"""


class Hub(object):
    def __init__(self):
        # Should load the subscribsers/topics out of the DB here.
        pass

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

