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

import optparse
import textwrap
import transaction
import sys

from pyramid.paster import bootstrap
from pyramid.request import Request


def register_listener():
    description = """
    Registers a listener URL with the hub. Useful for
    'bootstrapping' a hub with a default listener.

    Arguments:
        config_uri: the pyramid configuration to use for the hub
        listener_url: the URl to use as the listener callback

    Example usage:
        bin/reg_listener etc/paster.ini#pushhub http://localhost/update_feed
    """
    usage = "%prog config_uri listener_url"
    parser = optparse.OptionParser(
        usage=usage,
        description=textwrap.dedent(description),
    )

    options, args = parser.parse_args(sys.argv[1:])
    if not len(args) >= 2:
        print("You must provide a configuration file and a URL")
        return 2
    config_uri = args[0]
    listener_url = args[1]
    request = Request.blank('/', base_url='http://localhost/hub/')
    env = bootstrap(config_uri, request=request)

    hub = env['root']

    hub.register_listener(listener_url)
    transaction.commit()
    print "Registered listener for %s" % listener_url

    env['closer']()


def fetch_all_topics():
    description = """
    Attempts to fetch content for all topics that have been marked as failed
    previously. If the fetch fails during this run, it will not be retried
    until the script is called again.

    Arguments:
        config_uri: the pyramid configuration to use for the hub
        hub_url: the address of the hub that will be reported on topic fetch.

    Example usage:
        bin/fetch_all_topics etc/paster.ini#pushhub myhub.com

    """

    usage = "%prog config_uri hub_url"
    parser = optparse.OptionParser(
        usage=usage,
        description=textwrap.dedent(description)
    )

    options, args = parser.parse_args(sys.argv[1:])
    if not len(args) >= 2:
        print("You must provide a configuration file and a hub url")
        return
    config_uri = args[0]
    hub_url = args[1]

    request = Request.blank('/', base_url='http://localhost/hub')
    env = bootstrap(config_uri, request=request)

    hub = env['root']

    hub.fetch_all_content(hub_url)

    transaction.commit()

    env['closer']()


def show_subscribers():
    description = """
    Lists the current subscriber callback URLs registered with the hub.
    Arguments:
        config_uri: the pyramid configuration to use for the hub

    Example usage:
        bin/show_subscribers etc/paster.ini#pushhub

    """

    usage = "%prog config_uri"
    parser = optparse.OptionParser(
        usage=usage,
        description=textwrap.dedent(description)
    )

    options, args = parser.parse_args(sys.argv[1:])
    if not len(args) >= 1:
        print("You must provide a configuration file.")
        return
    config_uri = args[0]

    request = Request.blank('/', base_url='http://localhost/hub')
    env = bootstrap(config_uri, request=request)

    hub = env['root']

    subscriber_urls = [v.callback_url for v in hub.subscribers.values()]
    listener_urls = [v.callback_url for v in hub.listeners.values()]

    print "Subscriber URLs:"
    print "----------------"
    print "\n".join(subscriber_urls)

    print "\n"

    print "Listener URLs:"
    print "----------------"
    print "\n".join(listener_urls)
    env['closer']()


def show_topics():
    description = """
    Lists the current topic URLs registered with the hub.
    Arguments:
        config_uri: the pyramid configuration to use for the hub

    Example usage:
        bin/show_topics etc/paster.ini#pushhub

    """

    usage = "%prog config_uri"
    parser = optparse.OptionParser(
        usage=usage,
        description=textwrap.dedent(description)
    )

    options, args = parser.parse_args(sys.argv[1:])
    if not len(args) >= 1:
        print("You must provide a configuration file.")
        return
    config_uri = args[0]

    request = Request.blank('/', base_url='http://localhost/hub')
    env = bootstrap(config_uri, request=request)

    hub = env['root']

    topics = [v for v in hub.topics.values()]

    print "Topic URLs:"
    print "-----------"
    for topic in topics:
        print "%s\t%s" % (topic.url, topic.timestamp)

    env['closer']()
