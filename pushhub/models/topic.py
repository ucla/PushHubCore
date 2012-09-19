"""
A topic is a link published to the hub.

It has a last-updated timestamp, as well as the last-seen content for
generating diffs, so the hub knows what to send out to subscribers.
"""

from datetime import datetime
from urlparse import urlparse

from feedparser import parse
from persistent import Persistent
import requests
from repoze.folder import Folder
from zope.interface import Interface, implements
from webhelpers import feedgenerator
from zc.queue import Queue

from ..utils import FeedComparator


class Topics(Folder):
    title = u"Topics"


class ITopic(Interface):
    """Marker interface for topics."""
    pass


class Topic(Persistent):
    implements(ITopic)

    def __init__(self, url):
        """Initialize the topic and it's timestamp/content.
        Verification happens afterward.
        """

        # Do some basic sanity checks

        pieces = urlparse(url)

        if not (pieces.scheme and pieces.netloc and pieces.path):
            raise ValueError

        self.url = url
        self.timestamp = None
        self.content_type = ''
        self.content = None
        self.changed = False
        self.subscribers = Folder()
        self.subscriber_count = 0
        self.last_pinged = None
        self.ping()

    def fetch(self, hub_url):
        """Fetches the content from the publisher's provided URL"""

        user_agent = "PuSH Hub (+%s; %s)" % (hub_url, self.subscriber_count)

        headers = {'User-Agent': user_agent}

        response = requests.get(self.url, headers=headers)

        parsed = self.parse(response.content)

        if not parsed or parsed.bozo:
            # Should probably set a flag or log something here, too.
            raise ValueError

        if not self.content:
            newest_entries = parsed
            self.changed = True
        else:
            parsed_old = self.parse(self.content)
            # assemble_newest_entries will set changed flag if this isn't
            # the first fetch
            newest_entries = self.assemble_newest_entries(parsed, parsed_old)

        if not self.content_type:
            self.content_type = parsed.version

        if self.changed and self.content:
            self.content = self.generate_feed(newest_entries)
        else:
            self.content = response.content

        self.timestamp = datetime.now()

    def parse(self, content):
        """Parses a feed into a Python object"""
        if not content:
            return None
        parsed = parse(content)

        return parsed

    def ping(self):
        """Registers the last time a publisher pinged the hub for this topic."""
        self.last_pinged = datetime.now()

    def add_subscriber(self, subscriber):
        """Increment subscriber count so reporting on content fetch is easier.
        """
        self.subscriber_count += 1
        self.subscribers.add(subscriber.callback_url, subscriber)

    def remove_subscriber(self, subscriber):
        """Sanely remove subscribers from the count
        """
        self.subscribers.remove(subscriber.callback_url)
        if self.subscriber_count <= 0:
            raise ValueError
        self.subscriber_count -= 1

    def assemble_newest_entries(self, parsed, parsed_old):
        if not parsed or not parsed_old:
            return None
        compare = FeedComparator(parsed, parsed_old)
        new_entries = compare.new_entries()
        updated_entries = compare.updated_entries()
        metadata = compare.changed_metadata()

        if new_entries or updated_entries or metadata:
            self.changed = True

        all_entries = new_entries + updated_entries
        all_entries.sort(reverse=True, key=lambda entry: entry.updated_parsed)

        metadata['entries'] = all_entries

        return metadata

    def generate_feed(self, parsed_feed):
        new_feed = feedgenerator.Atom1Feed(
            title = parsed_feed['feed']['title'],
            link = parsed_feed['feed']['link'],
            description = parsed_feed['feed']['link'],
            author = parsed_feed['feed']['author']
        )
        for entry in parsed_feed.entries:
            new_feed.add_item(
                entry.pop('title'),
                entry.pop('link'),
                entry.pop('description', ''),
                **entry
            )

        return new_feed.writeString(parsed_feed['encoding'])

    def notify_subscribers(self, queue):
        """
        Notify subscribers to this topic that the feed has been updated.

        This will put the following data into a queue:
            Subscriber callback URL
            The feed content type
            The updated feed entries

        The queue can process the requests as long as it has this information.
        """

        if not self.subscribers:
            return

        c_type = None
        if 'atom' in self.content_type:
            c_type = 'application/atom+xml'
        elif 'rss' in self.content_type:
            c_type = 'application/rss+xml'

        if c_type is None:
            raise ValueError(
                'Invalid content type. Only Atom or RSS are supported'
            )

        headers = [('Content-Type', c_type)]
        body = self.content

        for url, subsciber in self.subscribers.items():
            queue.put({
                'callback': url,
                'headers': headers,
                'body': body,
                'max_tries': 10
            })
