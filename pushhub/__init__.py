from pyramid.config import Configurator
from pyramid_zodbconn import get_connection

from .views import publish

def root_factory(request):
    conn = get_connection(request)
    return appmaker(conn.root())

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    # XXX: The Hub will need to initialize here, most likely.
    # perhaps it can be attached to the request, so it's accessible from
    # all the views?
    config = Configurator(root_factory=root_factory, settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('publish', '/publish')
    config.add_view(publish, route_name='publish')

    return config.make_wsgi_app()
