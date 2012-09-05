from zope.component import getUtility

from pyramid.httpexceptions import exception_response

from .hub import IHub
from .utils import require_post


@require_post
def publish(request):
    hub = getUtility(IHub)
    content_type = request.headers.get('Content-Type', None)

    if (content_type != "application/x-www-form-urlencoded"):
        return exception_response(406)

    return exception_response(204)
