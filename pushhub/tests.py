import unittest

from pyramid import testing
from pyramid.testing import DummyRequest
from pyramid.url import urlencode

from pyramid.request import Request

from .views import publish, subscribe
from .models.topic import Topic

class BaseTest(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def r(self, url, headers=[], POST={}):
        if not headers:
            headers = [("Content-Type", "application/x-www-form-urlencoded")]
        return Request.blank(url,
                            headers=headers,
                            POST=POST)

class PublishTests(BaseTest):
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

    def test_publish_content_type(self):
        headers = [("Content-Type", "application/x-www-form-urlencoded")]
        request = Request.blank('/publish', headers, POST={})
        info = publish(request)
        self.assertEqual(info.status_code, 204)

    def test_publish_wrong_method(self):
        headers = [("Content-Type", "application/x-www-form-urlencoded")]
        request = Request.blank('', headers)
        info = publish(request)
        self.assertEqual(info.status_code, 405)
        self.assertEqual(info.headers['Allow'], 'POST')

class SubscribeTests(BaseTest):
    default_data = {
        'hub.verify':'sync',
        'hub.callback':'http://www.google.com'
    }

    def test_subscribe(self):
        request = Request.blank('/subscribe')
        info = subscribe(request)
        self.assertEqual(info.status_code, 405)

    def test_invalid_content_type(self):
        headers = [("Content-Type", "text/plain")]
        request = self.r('/subscribe', 
                        headers=headers, 
                        POST={"thing":"thing"})
        info = subscribe(request)
        self.assertEqual(info.status_code, 406)
        self.assertEqual(info.headers['Accept'], 
                'application/x-www-form-urlencoded')

    def test_invalid_verify_type(self):
        data = {"hub.verify": "bogus"}
        request = self.r('/subscribe',
                        POST=data)
        info = subscribe(request)
        self.assertEqual(info.status_code, 400)
        self.assertEqual(info.headers['Content-Type'], 'text/plain')
        self.assertTrue("hub.verify" in info.body)

    def test_sync_verify(self):
        data = self.default_data
        data.update({"hub.verify": "sync"})
        request = self.r('/subscribe',
                        POST=data)
        info = subscribe(request)
        self.assertEqual(info.status_code, 204)

    def test_multiple_verify_types(self):
        data = {
            'hub.verify':['async','sync'],
            'hub.callback':'http://www.google.com'
        }
        request = self.r('/subscribe',
                        POST=urlencode(data))
        info = subscribe(request)
        # should give preference to sync
        self.assertEqual(info.status_code, 204)
        data.update({'hub.verify': ['bogus','async']})
        request = self.r('/subscribe',
                        POST=urlencode(data))
        info = subscribe(request)
        self.assertEqual(info.status_code, 202)

    def test_multiple_invalid_verify_types(self):
        data = {"hub.verify": ['bogus', 'wrong']}
        request = self.r('/subscribe',
                        POST=urlencode(data))
        info = subscribe(request)
        self.assertEqual(info.status_code, 400)
        self.assertEqual(info.headers['Content-Type'], 'text/plain')
        self.assertTrue("hub.verify" in info.body)

    def test_invalid_callback(self):
        data = {
            'hub.verify':'sync',
            'hub.callback':'www.google.com'
        }
        request = self.r('/subscribe',
                        POST=data)
        info = subscribe(request)
        self.assertEqual(info.status_code, 400)
        self.assertTrue('hub.callback' in info.body)

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
