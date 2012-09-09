"""
Classes meant to represent the PubSubHubbub Hub.

The hub itself does not have state, but does hold references to
subscribers and topics.
"""
import random
import requests

from string import ascii_letters, digits

from zope.interface import Interface, implements
from repoze.folder import Folder

from .topic import Topics, Topic
from .subscriber import Subscribers, Subscriber


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
        topic = self.get_topic(topic_url)
        topic.ping()

    def notify_subscribers(self):
        """
        Sends updates to each of the subscribers to let them know
        of new topic content.
        """
        pass

    def subscribe(self, callback_url, topic_url):
        """
        Subscribe a subscriber to a topic

        Returns:
            True if subscription verification is successful, False otherwise.
        """
        topic = self.get_topic(topic_url)
        subscriber = self.get_subscriber(callback_url)

        verified = self.verify_subscription(subscriber, topic, "subscribe")
        if verified:
            try:
                subscriber.topics.add(topic_url, topic)
            except KeyError:
                # subscription already exists
                # this might mean an intent to renew lease
                pass
        return verified

    def unsubscribe(self, callback_url, topic_url):
        """
        Unsubscribe a subscriber to a topic

        """
        topic = self.get_topic(topic_url)
        subscriber = self.get_subscriber(callback_url)

        verified = self.verify_subscription(subscriber, topic, "unsubscribe")
        if verified:
            try:
                subscriber.topics.remove(topic_url, topic)
            except KeyError:
                # unsubcribed from this topic already
                pass
        return verified

    def verify_subscription(self, subscriber, topic, mode):
        """Verify that this is a real request by a subscriber.

        Args:
            subscriber: (Subscriber) The subscriber making the request
            topic: (Topic) The topic being subscribed to
            mode: (string) Either 'subscribe' or 'unsubscribe'

        Returns:
            True if intent is verified, False otherwise
        """
        challenge = self.get_challenge_string()
        qs = {
            "hub.mode": mode,
            "hub.topic": topic.url,
            "hub.challenge": challenge
        }
        r = requests.get(subscriber.callback_url, params=qs)
        if not r.status_code == requests.codes.ok:
            return False

        if challenge not in r.text:
            return False

        return True

    def get_topic(self, topic_url):
        """
        Retrieve or create a topic
        """
        if not self.topics:
            self.topics = Topics()

        topic = self.topics.get(topic_url, None)

        if not topic:
            topic = Topic(topic_url)
            self.topics.add(topic_url, topic)

        return topic

    def get_subscriber(self, callback_url):
        """
        Retrieve or create a subscriber
        """
        if not self.subscribers:
            self.subscribers = Subscribers()

        subscriber = self.subscribers.get(callback_url, None)

        if not subscriber:
            subscriber = Subscriber(callback_url)
            self.subscribers.add(callback_url, subscriber)

        return subscriber

    def get_challenge_string(self):
        """Generates a random challenge string"""
        choices = ascii_letters + digits
        return ''.join(random.choice(choices) for i in xrange(128))
