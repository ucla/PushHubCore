"""
Classes meant to represent the PubSubHubbub Hub.

The hub itself does not have state, but does hold references to
subscribers and topics.
"""

from zope.component import provideUtility
from zope.interface import Interface, implements

from pyramid.request import Request

from .utils import root_factory


def configure_hub(config, hub_impl=None):
    """Registers a hub implementation logic as a ZCA utility.

    This should be called by the application Configurator in
    order to register the Hub at initilization.

    An alternative implementation can be provided, mostly for
    testing purposes.
    """

    # A dummy request that allows us to call in to the root factory
    dummy_request = Request.blank('')
    dummy_request.registry = config.registry

    root = root_factory(dummy_request)
    topics = root['topics']
    subscribers = root['subscribers']

    if not hub_impl:
        provideUtility(Hub(topics, subscribers), provides=IHub)
        return
    provideUtility(hub_impl(topics, subscribers), provides=IHub)


class IHub(Interface):
    """Marker interface for hub implementations"""
    pass


class Hub(object):
    implements(IHub)

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
