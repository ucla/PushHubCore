from pyramid.config import Configurator

from .views import publish
from .utils import root_factory



def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(root_factory=root_factory, settings=settings)

    # Insert the hub in to the app-global registry as a singleton utility.
    config.hook_zca()
    config.include('.hub.configure_hub')

    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('publish', '/publish')
    config.add_view(publish, route_name='publish')
    return config.make_wsgi_app()
