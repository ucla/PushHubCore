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

    if not topic_mode or topic_mode != 'publish':
        return exception_response(400)

    if not topic_urls:
        return exception_response(400)

    return exception_response(204)

@require_post
def subscribe(request):
    # required
    callback = request.POST.get('hub.callback', '')
    topic = request.POST.get('hub.topic', '')
    verify_type_list = [s.lower() for s in request.POST.getall('hub.verify')]
    mode = request.POST.get('hub.mode', '').lower()
    # optional, per the spec we can support these or not.
    verify_token = unicode(request.POST.get('hub.verify_token', ''))
    secret = unicode(request.POST.get('hub.secret', '')) or None
    lease_seconds = (
       request.POST.get('hub.lease_seconds', '') or str(DEFAULT_LEASE_SECONDS))

    error_message = None

    error_message = None
    if not callback or not is_valid_url(callback):
      error_message = ('Invalid parameter: hub.callback; '
                       'must be valid URI with no fragment and '
                       'optional port %s' % ','.join(VALID_PORTS))
    else:
      callback = normalize_iri(callback)

    enabled_types = [vtype for vtype in verify_type_list
            if vtype in ('async', 'sync')]
    if not enabled_types:
      error_message = 'Invalid values for hub.verify: %s' % (verify_type_list,)
    else:
      verify_type = enabled_types

    if error_message:
      return exception_response(400,
                     body=error_message,
                     headers=[("Content-Type", "text/plain")]
                     )

    # save or retrieve subscription
    # give preference to sync
    if 'sync' in verify_type:
        # verify subscription now
        # if valid, return 204 else 409
        pass
    else:
        # can put it in a queue to process later, return Accepted
        # assuming some celery tasks make sense here
        return exception_response(202)

    # verified and active
    return exception_response(204)

