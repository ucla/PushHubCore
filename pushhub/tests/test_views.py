import unittest

from paste.util.multidict import MultiDict
from pyramid import testing
from pyramid.request import Request

from ..models import Hub
from ..views import publish, subscribe


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        # Create an in-memory instance of the hub so requests can use it
        self.root = Hub()

    def tearDown(self):
        testing.tearDown()
        self.root = None

    def r(self, url, headers=[], POST={}):
        if not headers:
            headers = [("Content-Type", "application/x-www-form-urlencoded")]
        req = Request.blank(url,
                            headers=headers,
                            POST=POST)
        req.root = self.root
        return req


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
        request = self.r('/publish', headers, POST={})
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
        request = self.r('/publish', headers, POST=data)
        info = publish(request)
        self.assertEqual(info.status_code, 204)

    def test_publish_content_type_with_incorrect_mode(self):
        headers = [("Content-Type", "application/x-www-form-urlencoded")]
        data = {'hub.mode': 'bad'}
        request = self.r('/publish', headers, POST=data)
        info = publish(request)
        self.assertEqual(info.status_code, 400)

    def test_publish_with_no_urls(self):
        data = {'hub.mode': 'publish'}
        request = self.r('/publish', self.valid_headers, POST=data)
        info = publish(request)
        self.assertEqual(info.status_code, 400)

    def test_publish_with_multiple_urls(self):
        data = MultiDict({'hub.mode': 'publish'})
        data.add('hub.url', 'http://www.example.com/')
        data.add('hub.url', 'http://www.site.com/')
        request = self.r('/publish', self.valid_headers, POST=data)
        info = publish(request)
        self.assertEqual(info.status_code, 204)


class SubscribeTests(BaseTest):
    default_data = MultiDict({
        'hub.verify': 'sync',
        # returns GET data so it will return the
        # hubs challenge string during verification
        'hub.callback': 'http://httpbin.org/get',
        'hub.mode': "subscribe",
        'hub.topic': "http://www.google.com/"
    })

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

    def test_multiple_verify_types_one_valid(self):
        data = self.default_data.copy()
        del data["hub.verify"]
        data.add('hub.verify', 'bogus')
        data.add('hub.verify', 'sync')
        request = self.r(
            '/subscribe',
            POST=data
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 204)

    def test_multiple_invalid_verify_types(self):
        data = self.default_data.copy()
        del data["hub.verify"]
        data.add('hub.verify', 'bad')
        data.add('hub.verify', 'wrong')
        request = self.r(
            '/subscribe',
            POST=data
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 400)
        self.assertEqual(info.headers['Content-Type'], 'text/plain')
        self.assertTrue("hub.verify" in info.body)

    def test_invalid_callback(self):
        data = self.default_data.copy()
        del data['hub.callback']
        data.add("hub.callback", "www.google.com")
        request = self.r(
            '/subscribe',
            POST=data
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 400)
        self.assertTrue('hub.callback' in info.body)

    def test_valid_callback(self):
        data = self.default_data.copy()
        request = self.r(
            '/subscribe',
            POST=data
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 204)

    def test_invalid_mode(self):
        data = self.default_data.copy()
        del data['hub.mode']
        data.add('hub.mode', 'bad')
        request = self.r(
            '/subscribe',
            POST=data,
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 400)
        self.assertTrue('hub.mode' in info.body)

    def test_valid_mode(self):
        data = self.default_data.copy()
        request = self.r(
            '/subscribe',
            POST=data
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 204)

    def test_valid_topic(self):
        data = self.default_data.copy()
        request = self.r(
            '/subscribe',
            POST=data
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 204)

    def test_invalid_topic(self):
        data = self.default_data.copy()
        del data['hub.topic']
        data.add('hub.topic', 'http://google.com/#fragment')
        request = self.r(
            '/subscribe',
            POST=data
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 400)
        self.assertTrue('hub.topic' in info.body)

    def test_not_verified_subscription(self):
        data = self.default_data.copy()
        del data["hub.callback"]
        data.add('hub.callback', 'http://httpbin.org/status/404')
        request = self.r(
            '/subscribe',
            POST=data
        )
        info = subscribe(request)
        self.assertEqual(info.status_code, 409)
