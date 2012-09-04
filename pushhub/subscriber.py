"""
Classes that describe subscribers to the Hub's topics.

Subscribers have a list of topics they are subscribed to, and callback URL
that will be hit when any of those topics are updated.
"""


# Will need to change to inherit from persistent.Persistent
class Subscriber(object):
    def __init__(self, callback_url):
        self.callback_url = callback_url
        self.topics = []
