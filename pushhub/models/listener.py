"""
Listeners are subscribers that wish to be notified any time
a new topic is added to the hub.
"""

from persistent import Persistent
from repoze.folder import Folder
import requests

from zope.interface import Interface, implements

from ..utils import is_valid_url

class Listeners(Folder):
    """Folder to hold listeners"""
    title = "Listeners"


class IListener(Interface):
    """Marker interface for listeners"""
    pass


class Listener(Persistent):
    implements(IListener)

    def __init__(self, callback_url):
        if not is_valid_url(callback_url):
            raise ValueError
        self.callback_url = callback_url

    def notify(self, topic_url):
        data = {'topic': topic_url}
        response = requests.get(self.callback_url, data=data)
        return response
