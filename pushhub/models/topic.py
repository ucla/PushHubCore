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
A topic is a link published to the hub.

It has a last-updated timestamp, as well as the last-seen content for
generating diffs, so the hub knows what to send out to subscribers.
"""

from datetime import datetime
from urlparse import urlparse

from feedparser import parse
from persistent import Persistent
import requests
from requests.exceptions import ConnectionError
from repoze.folder import Folder
from zope.interface import Interface, implements
from time import mktime
from redis import Redis
from rq import Queue

from ..utils import FeedComparator
from ..utils import Atom1FeedKwargs

import logging
logger = logging.getLogger(__name__)


class Topics(Folder):
    title = u"Topics"


class ITopic(Interface):
    """Marker interface for topics."""
    pass


class Topic(Persistent):
    implements(ITopic)

    def __repr__(self):
        return "<Topic %s>" % self.url

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
        self.failed = False
        self.ping()

    def fetch(self, hub_url):
        """Fetches the content from the publisher's provided URL"""

        user_agent = "PuSH Hub (+%s; %s)" % (hub_url, self.subscriber_count)

        headers = {'User-Agent': user_agent}

        try:
            response = requests.get(self.url, headers=headers)
            self.failed = False
        except ConnectionError:
            logger.warning('Could not connect to topic URL %s' % self.url)
            self.failed = True
            return

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
        logger.info('Fetched content for topic %s', self.url)

    def parse(self, content):
        """Parses a feed into a Python object"""
        if not content:
            return None
        parsed = parse(content)

        return parsed

    def ping(self):
        """Registers the last time a publisher pinged the hub for this topic.
        """
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
        logger.debug('%s new entries, %s updated entries in %s'
                     % (len(new_entries), len(updated_entries), self.url))
        metadata = compare.changed_metadata()

        if new_entries or updated_entries or metadata:
            self.changed = True

        all_entries = new_entries + updated_entries
        all_entries.sort(reverse=True, key=lambda entry: entry.updated_parsed)

        metadata['entries'] = all_entries

        return metadata

    def generate_feed(self, parsed_feed):
        self_links = [link['href'] for link
                     in parsed_feed['feed']['links']
                     if link['rel'] == u'self']
        if len(self_links) > 0:
            self_link = self_links[0]
        else:
            self_link = parsed_feed['feed']['link']

        new_feed = Atom1FeedKwargs(
            title=parsed_feed['feed']['title'],
            link=self_link,
            description=parsed_feed['feed']['link'],
            author=parsed_feed['feed'].get('author', u'Hub Aggregator')
        )
        for entry in parsed_feed.entries:
            updated = datetime.fromtimestamp(mktime(entry['updated_parsed']))

            try:
                entry['title']
            except KeyError:
                continue

            new_feed.add_item(
                entry.pop('title'),
                entry.pop('link'),
                entry.pop('summary', ''),
                pubdate=updated,
                unique_id=entry.pop('id', ''),
                author_name=entry.pop('author', ''),
                category=entry.pop('tags', []),
                **entry
            )
        string = new_feed.writeString(parsed_feed['encoding'])
        return string

    def get_request_data(self):
        """
        Return headers and body content useful for sending to a
        subscriber or listener
        """
        c_type = None
        if 'atom' in self.content_type:
            c_type = 'application/atom+xml'
        elif 'rss' in self.content_type:
            c_type = 'application/rss+xml'

        if c_type is None:
            raise ValueError(
                'Invalid content type. Only Atom or RSS are supported'
            )

        headers = {'Content-Type': c_type}
        body = self.content

        return (headers, body)

    def notify_subscribers(self):
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

        if not self.changed:
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

        q = Queue(connection=Redis())

        headers = {'Content-Type': c_type}
        body = self.content

        for url, subscriber in self.subscribers.items():
            q.enqueue('ucla.jobs.hub.post', url, body, headers)
            logger.debug('Item placed on subscriber queue %s' % (url))

        # We've notified all of our subscribers,
        # so we can set the flag to not notify them again
        # until another change
        self.changed = False
