import datetime
import unittest

from paste.util.multidict import MultiDict
from pyramid import testing
from pyramid.testing import DummyRequest
from pyramid.url import urlencode

from pyramid.request import Request

from .views import publish, subscribe
from .models.hub import Hub
from .models.topic import Topic


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def r(self, url, headers=[], POST={}):
        if not headers:
            headers = [("Content-Type", "application/x-www-form-urlencoded")]
        return Request.blank(
            url,
            headers=headers,
            POST=POST
        )


class PublishTests(BaseTest):

    valid_headers = [("Content-Type", "application/x-www-form-urlencoded")]

    def test_publish(self):
        request = Request.blank('/publish')
        info = publish(request)
        self.assertEqual(info.status_code, 405)

    def test_publish_wrong_type(self):
        """Post using an incorrect Content-Type"""
        headers = [('Content-Type', 'application/xml')]
        request = Request.blank('/publish',
                                headers=headers,
                                POST={'thing': 'thing'})
        info = publish(request)
        self.assertEqual(info.status_code, 406)

    def test_publish_content_type_without_mode(self):
        headers = [("Content-Type", "application/x-www-form-urlencoded")]
        request = Request.blank('/publish', headers, POST={})
        info = publish(request)
        self.assertEqual(info.status_code, 400)

    def test_publish_wrong_method(self):
        headers = [("Content-Type", "application/x-www-form-urlencoded")]
        request = Request.blank('', headers)
        info = publish(request)
        self.assertEqual(info.status_code, 405)
        self.assertEqual(info.headers['Allow'], 'POST')

    def test_publish_content_type_with_correct_mode(self):
        headers = [("Content-Type", "application/x-www-form-urlencoded")]
        data = {'hub.mode': 'publish', 'hub.url': 'http://www.google.com/'}
        request = Request.blank('/publish', headers, POST=data)
        info = publish(request)
        self.assertEqual(info.status_code, 204)

    def test_publish_content_type_with_incorrect_mode(self):
        headers = [("Content-Type", "application/x-www-form-urlencoded")]
        data = {'hub.mode': 'bad'}
        request = Request.blank('/publish', headers, POST=data)
        info = publish(request)
        self.assertEqual(info.status_code, 400)

    def test_publish_with_no_urls(self):
        data = {'hub.mode': 'publish'}
        request = Request.blank('/publish', self.valid_headers, POST=data)
        info = publish(request)
        self.assertEqual(info.status_code, 400)

    def test_publish_with_multiple_urls(self):
        data = MultiDict({'hub.mode': 'publish'})
        data.add('hub.url', 'http,//www.example.com')
        data.add('hub.url', 'http,//www.site.com')
        request = Request.blank('/publish', self.valid_headers, POST=data)
        info = publish(request)
        self.assertEqual(info.status_code, 204)


class SubscribeTests(BaseTest):
    default_data = {
        'hub.verify': 'sync',
        'hub.callback': 'http://www.google.com'
    }

    def test_subscribe(self):
        request = Request.blank('/subscribe')
        info = subscribe(request)
        self.assertEqual(info.status_code, 405)

    def test_invalid_content_type(self):
        headers = [("Content-Type", "text/plain")]
        request = self.r(
            '/subscribe',
            headers=headers,
            POST={"thing": "thing"}
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 406)
        self.assertEqual(
            info.headers['Accept'],
            'application/x-www-form-urlencoded'
        )

    def test_invalid_verify_type(self):
        data = {"hub.verify": "bogus"}
        request = self.r(
            '/subscribe',
            POST=data
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 400)
        self.assertEqual(info.headers['Content-Type'], 'text/plain')
        self.assertTrue("hub.verify" in info.body)

    def test_sync_verify(self):
        data = self.default_data
        data.update({"hub.verify": "sync"})
        request = self.r(
            '/subscribe',
            POST=data
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 204)

    def test_multiple_verify_types(self):
        data = {
            'hub.verify': ['async', 'sync'],
            'hub.callback': 'http://www.google.com'
        }
        request = self.r(
            '/subscribe',
            POST=urlencode(data)
        )
        info = subscribe(request)
        # should give preference to sync
        self.assertEqual(info.status_code, 204)
        data.update({'hub.verify': ['bogus', 'async']})
        request = self.r(
            '/subscribe',
            POST=urlencode(data)
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 202)

    def test_multiple_invalid_verify_types(self):
        data = {"hub.verify": ['bogus', 'wrong']}
        request = self.r(
            '/subscribe',
            POST=urlencode(data)
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 400)
        self.assertEqual(info.headers['Content-Type'], 'text/plain')
        self.assertTrue("hub.verify" in info.body)

    def test_invalid_callback(self):
        data = {
            'hub.verify': 'sync',
            'hub.callback': 'www.google.com'
        }
        request = self.r(
            '/subscribe',
            POST=data
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 400)
        self.assertTrue('hub.callback' in info.body)

    def test_valid_callback(self):
        data = self.default_data
        request = self.r(
            '/subscribe',
            POST=data
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 204)


class TopicTests(unittest.TestCase):

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


class HubTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_creation(self):
        hub = Hub()
        self.assertEqual(hub.topics, None)
        self.assertEqual(hub.subscribers, None)

    def test_publish_topic(self):
        hub = Hub()
        hub.publish('http://www.google.com/')
        self.assertEqual(len(hub.topics), 1)
        self.assertTrue('http://www.google.com/' in hub.topics.keys())
        self.assertEqual(
            hub.topics['http://www.google.com/'].url, 
            'http://www.google.com/'
        )

    def test_publish_existing_topic(self):
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

