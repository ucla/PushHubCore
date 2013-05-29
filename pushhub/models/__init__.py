"""
Copyright (c) 2013, Regents of the University of California
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

  * Redistributions of source code must retain the above copyright notice,
    this list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

  * Neither the name of the University of California nor the names of its
    contributors may be used to endorse or promote products derived from this
    software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from persistent.mapping import PersistentMapping

from .listener import Listeners
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

        listeners = Listeners()
        app_root.listeners = listeners
        topics.__name__ = 'listeners'
        topics.__parent__ = app_root

        import transaction
        transaction.commit()

    return zodb_root['app_root']
