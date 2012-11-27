from unittest import TestCase

from feedparser import parse

from .mocks import good_atom, updated_atom
from .mocks import no_author_good_atom, no_author_updated_atom

from ..utils import FeedComparator


class BaseComparatorTestCase(TestCase):
    old_parsed = parse(good_atom)
    new_parsed = parse(updated_atom)

    def setUp(self):
        self.compare = FeedComparator(self.new_parsed, self.old_parsed)

    def tearDown(self):
        self.compare = None


class TestFeedNew(BaseComparatorTestCase):

    def test_new_entries_length(self):
        new_entries = self.compare.new_entries()
        self.assertEqual(len(new_entries), 1)

    def test_new_entry_content(self):
        new_entries = self.compare.new_entries()
        self.assertEqual(new_entries[0]['title'], 'Colby Nolan')


class TestFeedUpdated(BaseComparatorTestCase):

    def test_updated_entries_length(self):
        updated_entries = self.compare.updated_entries()
        self.assertEqual(len(updated_entries), 2)

    def test_updated_entry_content(self):
        updated_entries = self.compare.updated_entries()
        entry = updated_entries[0]
        self.assertEqual(entry['title'], 'Heathcliff')
        content = entry['content'][0]
        self.assertTrue('This entry was changed!' in content['value'])

    def test_updated_link(self):
        updated_entries = self.compare.updated_entries()
        entry = updated_entries[1]
        self.assertEqual(entry['title'], 'Felix')
        self.assertEqual(entry['link'],
                         'http://publisher.example.com/happycat21.xml')


class TestFeedRemoved(BaseComparatorTestCase):

    def test_removed_entries_length(self):
        removed_entries = self.compare.removed_entries()
        self.assertEqual(len(removed_entries), 1)

    def test_removed_entry_content(self):
        removed_entries = self.compare.removed_entries()
        self.assertTrue(removed_entries[0]['title'], 'Nermal')


class TestFeedMetaDataChanged(BaseComparatorTestCase):

    def test_feed_tag_changed(self):
        changed_metadata = self.compare.changed_metadata()
        self.assertEqual(len(changed_metadata), 5)
        self.assertRaises(AttributeError, getattr, changed_metadata, 'entries')

    def test_feed_tag_title_changed(self):
        changed_metadata = self.compare.changed_metadata()
        self.assertEqual(changed_metadata['feed']['title'], 'Updated Feed')


class TestFeedNoAuthor(BaseComparatorTestCase):
    """This is the same as TestFeedMetaDataChanged, but with atom feeds
    with no author.
    """
    old_parsed = parse(no_author_good_atom)
    new_parsed = parse(no_author_updated_atom)

    def test_feed_tag_changed(self):
        changed_metadata = self.compare.changed_metadata()
        self.assertEqual(len(changed_metadata), 5)
        self.assertRaises(AttributeError, getattr, changed_metadata, 'entries')

    def test_feed_tag_title_changed(self):
        changed_metadata = self.compare.changed_metadata()
        self.assertEqual(changed_metadata['feed']['title'], 'Updated Feed')
