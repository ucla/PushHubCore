from persistent.mapping import PersistentMapping

from zc.queue import Queue

from .subscriber import Subscribers
from .topic import Topics
from .hub import Hub


class Root(PersistentMapping):
    __parent__ = __name__ = None


def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        app_root = Hub()
        zodb_root['app_root'] = app_root

        subscribers = Subscribers()
        app_root.subscribers = subscribers
        subscribers.__name__ = 'subscribers'
        subscribers.__parent__ = app_root

        topics = Topics()
        app_root.topics = topics
        topics.__name__ = 'topics'
        topics.__parent__ = app_root

        notify_queue = Queue()
        app_root.notify_queue = notify_queue
        notify_queue.__name__ = 'notify_queue'
        notify_queue.__parent__ = app_root
        import transaction
        transaction.commit()

    return zodb_root['app_root']
