import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'pyramid_zodbconn',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'ZODB3',
    'waitress',
    'repoze.folder',
    'zope.interface',
    'requests',
    'feedparser',
    'WebHelpers',
    'zc.queue',
    ]

setup(name='push-hub',
      version='0.11',
      description='push-hub',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Six Feet Up',
      author_email='info@sixfeetup.com',
      url='http://www.sixfeetup.com',
      keywords='web pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires = requires,
      tests_require= requires,
      extras_require={'test': ['mock']},
      test_suite="pushhub",
      entry_points = """\
      [paste.app_factory]
      main = pushhub:main
      [console_scripts]
      process_subscriber_notices = pushhub.scripts:process_subscriber_notices
      reg_listener = pushhub.scripts:register_listener
      fetch_all_topics = pushhub.scripts:fetch_all_topics
      """,
      )

