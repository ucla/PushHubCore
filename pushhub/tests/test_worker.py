from unittest import TestCase

from mock import patch

from zc.queue import Queue

from .mocks import good_atom, MockResponse, MultiResponse


from ..worker import notify_subscribers


class NotifySubscriberTest(TestCase):
    def setUp(self):
        self.queue = Queue()
        self.request_info = {
            'callback': 'http://www.site.com',
            # Needs to be a dict
            'headers': {'Content-Type': 'application/atom+xml'},
            'body': good_atom,
            'max_tries': 10
        }

    def tearDown(self):
        self.queue = None

    def test_good_call(self):
        self.queue.put(self.request_info)
        with patch('requests.post', new_callable=MockResponse, status_code=200):
            results = notify_subscribers(self.queue)
        self.assertEqual(results['http://www.site.com'], 200)
        self.assertEqual(len(self.queue), 0)

    def test_bad_responses(self):
        self.queue.put(self.request_info)
        with patch('requests.post', new_callable=MockResponse, status_code=404):
            results = notify_subscribers(self.queue)
        self.assertEqual(results['http://www.site.com'], 404)
        self.assertEqual(len(self.queue), 0)

    def test_multiple_successful_requests(self):
        self.queue.put(self.request_info)
        self.queue.put({'callback': 'http://www.example.com',
                        'headers': self.request_info['headers'],
                        'body': good_atom,
                        'max_tries': 10
        })
        urls = {
            'http://www.site.com': MockResponse(status_code=200),
            'http://www.example.com': MockResponse(status_code=200),
        }
        with patch('requests.post', new_callable=MultiResponse, mapping=urls):
            results = notify_subscribers(self.queue)
        self.assertEqual(len(results), 2)
        self.assertEqual(results['http://www.example.com'], 200)
