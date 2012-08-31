import unittest

from pyramid import testing
from pyramid.testing import DummyRequest

from pyramid.request import Request
from .views import publish


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

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
