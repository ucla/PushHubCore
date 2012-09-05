from persistent.mapping import PersistentMapping

from .subscriber import Subscribers
from .topic import Topics
from .hub import Hub


class Root(PersistentMapping):
    __parent__ = __name__ = None


def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        app_root = Root()
        zodb_root['app_root'] = app_root
        import transaction
        transaction.commit()

        subscribers = Subscribers()
        app_root['subscribers'] = subscribers
        subscribers.__name__ = 'subscribers'
        subscribers.__parent__ = app_root
        transaction.commit()

        topics = Topics()
        app_root['topics'] = topics
        topics.__name__ = 'topics'
        topics.__parent__ = app_root
        transaction.commit()

    return zodb_root['app_root']
