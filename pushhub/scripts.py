import optparse
import textwrap
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

    notify_subscribers(queue)

    env['closer']()
