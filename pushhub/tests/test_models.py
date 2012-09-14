from unittest import TestCase
from mock import patch

from feedparser import parse

from ..models.hub import Hub
from ..models.topic import Topic
from ..models.subscriber import Subscriber
from ..utils import is_valid_url

from .mocks import good_atom, MockResponse, MultiResponse, updated_atom


class SubscriberTests(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_creation(self):
        s = Subscriber('http://www.google.com')
        self.assertEqual(s.callback_url, 'http://www.google.com')

    def test_bad_urls(self):
        """
        A 'good' URL will have:
            * a scheme
            * a netloc (usually server, domain, and TLD names)
            * not only a path
            * no fragments
            # a valid port
        """
        self.assertRaises(ValueError, Subscriber, 'http://')
        self.assertRaises(ValueError, Subscriber, 'www.site.com')
        self.assertRaises(ValueError, Subscriber, '/path-only')
        self.assertRaises(
            ValueError,
            Subscriber,
            'http://google.com/#fragment'
        )


class TopicTests(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_creation(self):
        t = Topic('http://www.google.com/')
        self.assertEqual(t.url, 'http://www.google.com/')
        self.assertEqual(t.timestamp, None)
        self.assertEqual(t.content, None)

    def test_bad_urls(self):
        """
        A 'good' URL will have:
            * a scheme
            * a netloc (usually server, domain, and TLD names)
            * a path
        """
        self.assertRaises(ValueError, Topic, 'http://')
        self.assertRaises(ValueError, Topic, 'www.site.com')
        self.assertRaises(ValueError, Topic, '/path-only')

    def test_pinged_time(self):
        t = Topic('http://www.google.com/')
        original_time = t.last_pinged
        t.ping()
        new_time = t.last_pinged
        self.assertTrue(original_time < new_time)

    def test_adding_subscriber(self):
        t = Topic('http://www.google.com/')
        t.add_subscriber()
        self.assertEqual(t.subscribers, 1)

    def test_removing_subscriber(self):
        t = Topic('http://www.google.com/')
        t.add_subscriber()
        t.remove_subscriber()
        self.assertEqual(t.subscribers, 0)

    def test_removing_too_many_subscribers(self):
        t = Topic('http://www.google.com/')
        self.assertRaises(ValueError, t.remove_subscriber)

    def test_fetching_bad_content(self):
        t = Topic('http://httpbin.org/get')
        self.assertRaises(ValueError, t.fetch, 'http://myhub.com/')
        # Nothing should be changed if the fetch fails
        self.assertTrue(t.timestamp is None)
        self.assertTrue(t.content is None)

    @patch('requests.get', new_callable=MockResponse, content=good_atom)
    def test_fetching_good_content(self, mock):
        t = Topic('http://httpbin.org/get')
        t.fetch('http://myhub.com/')
        self.assertTrue('John Doe' in t.content)
        self.assertTrue(t.timestamp is not None)

    def test_verify_bad_content(self):
        t = Topic('http://httpbin.org/get')
        bad_content = 'this is bad'
        self.assertTrue(t.parse(bad_content).bozo)

    def test_verify_good_content(self):
        t = Topic('http://httpbin.org/get')
        self.assertFalse(t.parse(good_atom).bozo)

    def test_parse_good_content(self):
        """
        Basic sanity test for parsing.
        """
        t = Topic('http://httpbin.org/get')
        parsed = t.parse(good_atom)
        self.assertEqual(parsed['channel']['title'], 'Example Feed')
        self.assertEqual(len(parsed['items']), 4)


class TopicNewEntriesTests(TestCase):

    old_parsed = parse(good_atom)
    new_parsed = parse(updated_atom)

    def setUp(self):
        self.topic = Topic('http://www.google.com/')

    def tearDown(self):
        self.topic = None

    def test_assemble_newest_entries_returns(self):
        new_feed = self.topic.assemble_newest_entries(
                self.new_parsed,
                self.old_parsed
        )
        self.assertTrue(new_feed is not None)
        self.assertTrue('entries' in new_feed)

    def test_assembled_entries_are_correct(self):
        new_feed = self.topic.assemble_newest_entries(
                self.new_parsed,
                self.old_parsed
        )
        entries = new_feed['entries']
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].title, 'Colby Nolan')
        self.assertEqual(entries[1].title, 'Heathcliff')

    def test_assembled_entries_metadata(self):
        new_feed = self.topic.assemble_newest_entries(
            self.new_parsed,
            self.old_parsed
        )
        feed = new_feed['feed']
        self.assertEqual(feed['title'], 'Updated Feed')

    def test_parsed_output(self):
        parsed_feed = self.topic.assemble_newest_entries(
            self.new_parsed,
            self.old_parsed
        )
        output_str = self.topic.generate_feed(parsed_feed)
        self.assertTrue('Nermal' not in output_str)
        self.assertTrue('Heathcliff' in output_str)
        self.assertTrue('Updated Feed' in output_str)

    def test_no_input(self):
        parsed_feed = None
        self.assertRaises(TypeError, self.topic.generate_feed, parsed_feed)


class HubTests(TestCase):

    challenge = "abcdefg"

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_creation(self):
        hub = Hub()
        self.assertEqual(hub.topics, None)
        self.assertEqual(hub.subscribers, None)

    @patch('requests.get', new_callable=MockResponse, content=good_atom)
    def test_publish_topic(self, mock):
        hub = Hub()
        hub.publish('http://www.google.com/')
        self.assertEqual(len(hub.topics), 1)
        self.assertTrue('http://www.google.com/' in hub.topics.keys())
        self.assertEqual(
            hub.topics['http://www.google.com/'].url,
            'http://www.google.com/'
        )

    @patch('requests.get', new_callable=MockResponse, content=good_atom)
    def test_publish_existing_topic(self, mock):
        """
        Existing topics should have their 'pinged' time updated.
        """
        hub = Hub()
        hub.publish('http://www.google.com/')
        first_time = hub.topics['http://www.google.com/'].last_pinged
        hub.publish('http://www.google.com/')
        second_time = hub.topics['http://www.google.com/'].last_pinged
        self.assertEqual(len(hub.topics), 1)
        self.assertTrue(second_time > first_time)

    @patch.object(Hub, 'get_challenge_string')
    def test_subscribe(self, mock_get_challenge_string):
        hub = Hub()
        mock_get_challenge_string.return_value = self.challenge
        with patch('requests.get', new_callable=MockResponse,
                   content=self.challenge, status_code=200):
            hub.subscribe('http://httpbin.org/get', 'http://www.google.com/')
        self.assertEqual(len(hub.subscribers), 1)
        self.assertTrue('http://httpbin.org/get' in hub.subscribers.keys())
        self.assertEqual(
            hub.subscribers['http://httpbin.org/get'].callback_url,
            'http://httpbin.org/get'
        )

    @patch.object(Hub, 'get_challenge_string')
    def test_existing_subscription(self, mock_get_challenge_string):
        hub = Hub()
        mock_get_challenge_string.return_value = self.challenge
        with patch('requests.get', new_callable=MockResponse,
                   content=self.challenge, status_code=200):
            hub.subscribe('http://httpbin.org/get', 'http://www.google.com/')
            hub.subscribe('http://httpbin.org/get', 'http://www.google.com/')
        self.assertEqual(len(hub.subscribers), 1)
        sub = hub.get_or_create_subscriber('http://httpbin.org/get')
        self.assertEqual(len(sub.topics), 1)

    @patch.object(Hub, 'get_challenge_string')
    def test_unsubscribe(self, mock_get_challenge_string):
        hub = Hub()
        mock_get_challenge_string.return_value = self.challenge
        with patch('requests.get', new_callable=MockResponse,
                   content=self.challenge, status_code=200):
            hub.subscribe('http://www.google.com/', 'http://www.google.com/')
        sub = hub.get_or_create_subscriber('http://www.google.com/')
        self.assertEqual(len(sub.topics), 1)
        self.assertTrue('http://www.google.com/' in sub.topics.keys())
        with patch('requests.get', new_callable=MockResponse,
                   content=self.challenge, status_code=200):
            hub.unsubscribe('http://www.google.com/', 'http://www.google.com/')
        self.assertEqual(len(sub.topics), 0)
        # test repeated unsubscribe
        with patch('requests.get', new_callable=MockResponse,
                   content=self.challenge, status_code=200):
            hub.unsubscribe('http://www.google.com/', 'http://www.google.com/')
        self.assertEqual(len(sub.topics), 0)

    @patch('requests.get', new_callable=MockResponse, content=good_atom)
    def test_fetch_all_topics(self, mock):
        hub = Hub()
        hub.publish('http://httpbin.org/get')
        hub.publish('http://www.google.com/')
        hub.fetch_all_content('http://myhub.com')
        first = hub.topics.get('http://httpbin.org/get')
        second = hub.topics.get('http://www.google.com/')
        self.assertTrue(first.timestamp is not None)
        self.assertTrue('John Doe' in first.content)
        self.assertTrue(second.timestamp is not None)
        self.assertTrue('John Doe' in second.content)

    def test_fetch_all_topics_one_error(self):
        """Allow a test topic to fail; others should be unaffected
        """
        hub = Hub()
        hub.publish('http://httpbin.org/get')
        hub.publish('http://www.google.com/')
        urls = {
            'http://httpbin.org/get': MockResponse(content=good_atom),
            'http://www.google.com/': MockResponse(content="adslkfhadslfhd"),
        }
        with patch('requests.get', new_callable=MultiResponse, mapping=urls):
            hub.fetch_all_content('http://myhub.com')
        good = hub.topics.get('http://httpbin.org/get')
        bad = hub.topics.get('http://www.google.com/')

        self.assertTrue(good.timestamp is not None)
        self.assertTrue('John Doe' in good.content)

        self.assertTrue(bad.timestamp is None)
        self.assertTrue(bad.content is None)

    def test_fetch_some_content(self):
        hub = Hub()
        hub.publish('http://httpbin.org/get')
        hub.publish('http://www.google.com/')
        urls = {
            'http://httpbin.org/get': MockResponse(content=good_atom),
            'http://www.google.com/': MockResponse(content=good_atom),
        }
        with patch('requests.get', new_callable=MultiResponse, mapping=urls):
            hub.fetch_content([
                'http://httpbin.org/get',
                'http://www.google.com/'
            ], 'http://myhub.com')

        first = hub.topics.get('http://httpbin.org/get')
        second = hub.topics.get('http://www.google.com/')
        self.assertTrue(first.timestamp is not None)
        self.assertTrue('John Doe' in first.content)
        self.assertTrue(second.timestamp is not None)
        self.assertTrue('John Doe' in second.content)

    def test_fetch_some_failing_content(self):
        hub = Hub()
        hub.publish('http://httpbin.org/get')
        hub.publish('http://www.google.com/')
        urls = {
            'http://httpbin.org/get': MockResponse(content=good_atom),
            'http://www.google.com/': MockResponse(content="adslkfhadslfhd"),
        }
        with patch('requests.get', new_callable=MultiResponse, mapping=urls):
            hub.fetch_content([
                'http://httpbin.org/get',
                'http://www.google.com/'
            ], 'http://myhub.com')

        good = hub.topics.get('http://httpbin.org/get')
        bad = hub.topics.get('http://www.google.com/')

        self.assertTrue(good.timestamp is not None)
        self.assertTrue('John Doe' in good.content)

        self.assertTrue(bad.timestamp is None)
        self.assertTrue(bad.content is None)

    def test_fetch_some_content_no_response(self):
        hub = Hub()
        hub.publish('http://httpbin.org/get')
        hub.publish('http://www.google.com/')
        urls = {
            'http://httpbin.org/get': MockResponse(content=good_atom),
        }
        with patch('requests.get', new_callable=MultiResponse, mapping=urls):
            hub.fetch_content([
                'http://httpbin.org/get',
                'http://www.google.com/'
            ], 'http://myhub.com')

        good = hub.topics.get('http://httpbin.org/get')
        bad = hub.topics.get('http://www.google.com/')

        self.assertTrue(good.timestamp is not None)
        self.assertTrue('John Doe' in good.content)

        self.assertTrue(bad.timestamp is None)
        self.assertTrue(bad.content is None)

    def test_fetch_some_unpublished_content(self):
        hub = Hub()
        hub.publish('http://httpbin.org/get')
        urls = {
            'http://httpbin.org/get': MockResponse(content=good_atom),
            'http://www.google.com/': MockResponse(content="adslkfhadslfhd"),
        }
        with patch('requests.get', new_callable=MultiResponse, mapping=urls):
            hub.fetch_content([
                'http://httpbin.org/get',
                'http://www.google.com/'
            ], 'http://myhub.com')

        good = hub.topics.get('http://httpbin.org/get')
        bad = hub.topics.get('http://www.google.com/')

        self.assertTrue(good.timestamp is not None)
        self.assertTrue('John Doe' in good.content)

        self.assertTrue(bad is None)


class UtilTests(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_is_valid_url(self):
        """
        A 'good' URL will have:
            * a scheme
            * a netloc (usually server, domain, and TLD names)
            * not only a path
            * no fragments
            # a valid port
        """
        self.assertFalse(is_valid_url('google.com'))
        self.assertFalse(is_valid_url('http://google.com/#fragment'))
        # see .views.VALID_PORTS for a list of valid ports
        self.assertFalse(is_valid_url('https://www.google.com:8888'))
        self.assertFalse(is_valid_url("/path"))
        self.assertFalse(is_valid_url("http://"))
