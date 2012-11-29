import datetime
import optparse
import textwrap
import transaction
import sys

from pyramid.paster import bootstrap
from pyramid.request import Request

from pushhub.worker import notify_subscribers


def process_subscriber_notices():
    description = """
    Processes subscriber notifications waiting in the queue.

    This script is meant to be run as a cron job that will regularly
    send out notices of content updates to subscriber callback URLs.

    Pass in a paster settings ini file to determine the settings
    needed.
    """
    usage = "%prog config_uri"
    parser = optparse.OptionParser(
        usage=usage,
        description=textwrap.dedent(description),
    )

    options, args = parser.parse_args(sys.argv[1:])
    if not len(args) >= 1:
        print("You must provide a configuration file")
        return 2
    config_uri = args[0]
    request = Request.blank('/', base_url='http://localhost/hub/')
    env = bootstrap(config_uri, request=request)
    queue = env['root'].notify_queue

    results = notify_subscribers(queue)
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print "%s %s %s" % (now,  __name__, results)

    transaction.commit()
    env['closer']()


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
