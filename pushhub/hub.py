"""
Classes meant to represent the PubSubHubbub Hub.

The hub itself does not have state, but does hold references to
subscribers and topics.
"""

from zope.component import provideUtility
from zope.interface import Interface, implements


def configure_hub(config, hub_impl=None):
    """Registers a hub implementation logic as a ZCA utility.

    This should be called by the application Configurator in
    order to register the Hub at initilization.

    An alternative implementation can be provided, mostly for
    testing purposes.
    """
    if not hub_impl:
        provideUtility(Hub(), provides=IHub)
    provideUtility(hub_impl(), provides=IHub)


class IHub(Interface):
    """Marker interface for hub implementations"""
    pass


class Hub(object):
    implements(IHub)

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

