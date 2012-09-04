"""
A topic is a link published to the hub.

It has a last-updated timestamp, as well as the last-seen content for
generating diffs, so the hub knows what to send out to subscribers.
"""

class Topic(object):
    def __init__(self, url, timestamp, content):
        self.url = url
        self.timestamp = timestamp
        self.content = content
