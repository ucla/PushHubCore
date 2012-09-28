from pyramid.config import Configurator
from pyramid_zodbconn import get_connection

from .models import appmaker
from .views import listen, publish, subscribe


def root_factory(request):
    conn = get_connection(request)
    return appmaker(conn.root())


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(root_factory=root_factory, settings=settings)

    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('publish', '/publish')
    config.add_view(publish, route_name='publish')

    config.add_route('subscribe', '/subscribe')
    config.add_view(subscribe, route_name='subscribe')

    config.add_route('listen', '/listen')
    config.add_view(listen, route_name='listen')

    return config.make_wsgi_app()
