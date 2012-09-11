from os.path import abspath, dirname, join

path = abspath(dirname(__file__))

good_atom = open(join(path, 'fixtures', 'example.xml'), 'r').read()


class MockResponse(object):
    def __init__(self, content=None, headers=None, status_code=None):
        self.content = content
        self.headers = headers
        self.status_code = status_code

    def __call__(self, *args, **kwargs):
        return self


class MultiResponse(object):
    def __init__(self, mapping):
        self.mapping = mapping

    def __call__(self, url, *args, **kwargs):
        if url in self.mapping.keys():
            return self.mapping[url]
        else:
            return MockResponse(status_code=404)
