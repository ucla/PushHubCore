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

"""
Classes that describe subscribers to the Hub's topics.

Subscribers have a list of topics they are subscribed to, and callback URL
that will be hit when any of those topics are updated.
"""
from datetime import datetime

from persistent import Persistent
from repoze.folder import Folder
from zope.interface import Interface, implements

from pushhub.utils import is_valid_url
from .topic import Topics


class Subscribers(Folder):
    """Folder to hold our subscribers"""
    title = "Subscribers"


class ISubscriber(Interface):
    """Marker interface for subscribers"""
    pass


class Subscriber(Persistent):
    implements(ISubscriber)

    def __repr__(self):
        return "<Subscriber '%s'>" % self.callback_url

    def __init__(self, callback_url):
        if not is_valid_url(callback_url):
            raise ValueError
        self.callback_url = callback_url
        self.topics = Topics()
        self.created_date = datetime.now()
