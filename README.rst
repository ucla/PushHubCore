PushHubCore
===========

The PushHubCore package is an implementation of Google's proposed PubSubHubbub specification. It allows
'publishers' to provide URLs of RSS or Atom feeds (called 'topics') to the hub, and 
'subscribers' to register for notifications from the hub when those feeds are updated.

This implementation contains a Hub object that will be initialized at application startup, and
which holds a reference to the list of subscribers and the topics being tracked. Requests will
go to view functions which then manipulate or query this Hub object.

See the `PushHub`_ buildout for more information on how to get started.

.. _PushHub: https://github.com/ucla/PushHub#readme
