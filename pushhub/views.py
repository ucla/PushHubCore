from pyramid.httpexceptions import exception_response

from .utils import require_post, is_valid_url, normalize_iri

# Default expiration time of a lease.
DEFAULT_LEASE_SECONDS = (5 * 24 * 60 * 60)  # 5 days

VALID_PORTS = frozenset([
    '80', '443', '4443', '8080', '8081', '8082', '8083', '8084', '8085',
    '8086', '8087', '8088', '8089', '8188', '8444', '8990'])


@require_post
def publish(request):
    topic_mode = request.POST.get('hub.mode', '')
    topic_urls = request.POST.getall('hub.url')

    bad_data = False
    error_msg = None

    if not topic_mode or topic_mode != 'publish':
        bad_data = True
        error_msg = "Invalid or unspecified mode."

    if not topic_urls:
        bad_data = True
        error_msg = "No topic URLs provided"

    hub = request.root

    for topic_url in topic_urls:
        try:
            hub.publish(topic_url)
        except ValueError:
            bad_data = True
            error_msg = "Malformed URL: %s" % topic_url

    if not bad_data:
        hub.fetch_content(topic_urls, request.application_url)

    if bad_data and error_msg:
        return exception_response(400,
                                  body=error_msg,
                                  headers=[('Content-Type', 'text/plain')])
    hub.notify_subscribers()

    return exception_response(204)


@require_post
def subscribe(request):
    # required
    callback = request.POST.get('hub.callback', '')
    topic = request.POST.get('hub.topic', '')
    verify_type_list = [s.lower() for s in request.POST.getall('hub.verify')]
    mode = request.POST.get('hub.mode', '').lower()
    # optional, per the spec we can support these or not.
    # TODO: support for the following optional arguments
    verify_token = unicode(request.POST.get('hub.verify_token', ''))
    secret = unicode(request.POST.get('hub.secret', '')) or None
    lease_seconds = (
        request.POST.get('hub.lease_seconds', '') or
        str(DEFAULT_LEASE_SECONDS)
    )

    error_message = None
    if not callback or not is_valid_url(callback):
        error_message = (
            'Invalid parameter: hub.callback; '
            'must be valid URI with no fragment and '
            'optional port %s' % ','.join(VALID_PORTS)
        )
    else:
        callback = normalize_iri(callback)

    if not topic or not is_valid_url(topic):
        error_message = (
            'Invalid parameter: hub.topic; '
            'must be valid URI with no fragment and '
            'optional port %s' % ','.join(VALID_PORTS)
        )
    else:
        topic = normalize_iri(topic)

    if mode not in ('subscribe', 'unsubscribe'):
        error_message = (
            'Invalid parameter: hub.mode; '
            'Supported values are "subscribe", "unsubscribe"'
            'Given: %s' % mode
        )

    enabled_types = [
        vtype for vtype in verify_type_list
        if vtype in ('async', 'sync')
    ]

    if not enabled_types:
        error_message = (
            'Invalid values for hub.verify: %s' %
            (verify_type_list,)
        )
    else:
        verify_type = enabled_types

    if error_message:
        return exception_response(
            400,
            body=error_message,
            headers=[("Content-Type", "text/plain")]
        )

    hub = request.root

    # give preference to sync
    if 'sync' in verify_type:
        if mode == 'subscribe':
            verified = hub.subscribe(callback, topic)
        else:
            verified = hub.unsubscribe(callback, topic)

        if not verified:
            return exception_response(
                409,
                body="Subscription intent not verified",
                headers=[("Content-Type", "text/plain")]
            )
    else:
        # TODO: async verification
        # should return a 202 and then perform verification
        # at a later date as determined by the hub
        # we'll return a 400 right now until it's supported
        return exception_response(
            400,
            body="async verification currently not supported",
            headers=[("Content-Type", "text/plain")]
        )
    # verified and active
    return exception_response(204)
