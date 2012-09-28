import requests
from requests.exceptions import HTTPError

import logging
log = logging.getLogger(__name__)


def notify_subscribers(queue):
    """
    Notifies subscribers that topics in the queue have been updated.

    The queue will be populated by dictionaries with a minimum of the following
    keys:
        * callback - URL to send the request to
        * headers - HTTP headers
        * body  - Latest content from the feed.
    """

    results = {}
    while queue:
        request_info = queue.pull()
        if request_info['max_tries']:
            if request_info['max_tries'] <= 0:
                log.info(
                    "Could not reach callback: %s. (%s tries)" % (
                        request_info['callback'],
                        request_info['max_tries']
                        )
                    )
                # Needs logging that we passed max retries.
                continue
        data = {}
        data['feed'] = request_info['body']

        headers = request_info['headers']

        response = requests.post(
            request_info['callback'],
            headers=headers,
            data=data
        )
        results[request_info['callback']] = response.status_code
        try:
            response.raise_for_status()
        except HTTPError:
            if 'max_tries' in request_info:
                request_info['max_tries'] = request_info['max_tries'] - 1
                queue.put(request_info)

    return results
