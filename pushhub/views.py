from pyramid.httpexceptions import exception_response

from .utils import require_post


@require_post
def publish(request):
    content_type = request.headers.get('Content-Type', None)

    if (content_type != "application/x-www-form-urlencoded"):
        return exception_response(406)

    return exception_response(204)
