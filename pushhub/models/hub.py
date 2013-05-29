"""
Copyright (c) 2013, Regents of the University of California
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

  * Redistributions of source code must retain the above copyright notice,
    this list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

  * Neither the name of the University of California nor the names of its
    contributors may be used to endorse or promote products derived from this
    software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

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

from .listener import Listener, Listeners
from .topic import Topics, Topic
from .subscriber import Subscribers, Subscriber

import logging

logger = logging.getLogger(__name__)


class IHub(Interface):
    """Marker interface for hub implementations"""
    pass


class Hub(Folder):
    implements(IHub)
    __name__ = __parent__ = None
    title = "Hub"

    def __init__(self):
        super(Hub, self).__init__()
        self.topics = None
        self.subscribers = None
        self.listeners = Listeners()

    def publish(self, topic_url):
        """
        Publish a topic to the hub.
        """
        topic = self.get_or_create_topic(topic_url)
        topic.ping()
        logger.info('Published topic with URL %s' % topic_url)

    def notify_subscribers(self):
        """
        Sends updates to each topic's subscribers to let them know
        of new content.
        """
        if self.topics is None:
            return

        for url, topic in self.topics.items():
            logger.debug('Notify subscriber for topic: %s' % url)
            topic.notify_subscribers()

    def subscribe(self, callback_url, topic_url, verify_callbacks=True):
        """
        Subscribe a subscriber to a topic

        Returns:
            True if subscription verification is successful, False otherwise.
        """
        topic = self.get_or_create_topic(topic_url)
        subscriber = self.get_or_create_subscriber(callback_url)

        if verify_callbacks:
            verified = self.verify_subscription(subscriber, topic, "subscribe")
        else:
            verified = True

        if verified:
            try:
                subscriber.topics.add(topic_url, topic)
                topic.add_subscriber(subscriber)
                logger.info('Added subscriber with callback %s to topic %s' % (callback_url, topic_url))
            except KeyError:
                # subscription already exists
                # this might mean an intent to renew lease
                pass
        return verified

    def unsubscribe(self, callback_url, topic_url):
        """
        Unsubscribe a subscriber to a topic

        """
        topic = self.get_or_create_topic(topic_url)
        subscriber = self.get_or_create_subscriber(callback_url)

        verified = self.verify_subscription(subscriber, topic, "unsubscribe")
        if verified:
            try:
                subscriber.topics.remove(topic_url, topic)
                topic.remove_subscriber(subscriber)
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
            challenge: (string) A random string the subscriber must return
                in the request body

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

        if challenge not in r.content:
            return False

        return True

    def get_or_create_topic(self, topic_url):
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

    def get_or_create_subscriber(self, callback_url):
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

    def get_or_create_listener(self, callback_url):
        listener = self.listeners.get(callback_url, None)

        if not listener:
            listener = Listener(callback_url)
            self.listeners.add(callback_url, listener)

        return listener

    def get_challenge_string(self):
        """Generates a random challenge string"""
        choices = ascii_letters + digits
        return ''.join(random.choice(choices) for i in xrange(128))

    def fetch_all_content(self, hub_url, only_failed=False):
        """
        Fetches the content at all topic URLs.
        """
        topic_entries = self.topics.items()
        if only_failed:
            topic_entries = [t for t in self.topics.items() if t[1].failed]

        for topic_id, topic in topic_entries:
            try:
                topic.fetch(hub_url)
            except ValueError:
                continue

    def fetch_content(self, topic_urls, hub_url):
        """
        Takes a list of topic urls and attempts to fetch their content.
        """

        for topic_url in topic_urls:
            topic = self.topics.get(topic_url, None)

            if not topic:
                continue

            try:
                topic.fetch(hub_url)
            except ValueError:
                continue

    def register_listener(self, callback_url):
        listener = self.get_or_create_listener(callback_url)
        if not self.topics:
            return
        for topic in self.topics.values():
            if topic.url in listener.topics.keys():
                continue
            listener.topics.add(topic.url, topic)
            logger.info('Added listener %s to topic %s' % (callback_url,
                                                           topic.url))
            listener.notify(topic)
        logger.info('Registered listener with URL %s' % callback_url)

    def notify_listeners(self, topics):
        for topic in topics:
            for url, listener in self.listeners.items():
                if topic.url not in listener.topics.keys():
                    listener.topics.add(topic.url, topic)
                listener.notify(topic)
