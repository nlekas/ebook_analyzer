"""
Tests for HashProcessor abstract base class.
"""

import pytest

from ebook_calibre_analyzer.hashing.base import HashProcessor


class TestHashProcessor:
    """Test cases for HashProcessor abstract base class."""

    def test_is_abstract_base_class(self):
        """Test that HashProcessor is an abstract base class."""
        # Cannot instantiate abstract class
        with pytest.raises(TypeError):
            HashProcessor()  # type: ignore

    def test_hash_first_1k_is_abstract(self):
        """Test that hash_first_1k is an abstract method."""

        # Create a concrete class without implementing hash_first_1k
        class IncompleteProcessor(HashProcessor):
            def hash_full_file(self, file):
                pass

            def hash_batch(self, files, stage):
                pass

        with pytest.raises(TypeError):
            IncompleteProcessor()  # type: ignore

    def test_hash_full_file_is_abstract(self):
        """Test that hash_full_file is an abstract method."""

        # Create a concrete class without implementing hash_full_file
        class IncompleteProcessor(HashProcessor):
            def hash_first_1k(self, file):
                pass

            def hash_batch(self, files, stage):
                pass

        with pytest.raises(TypeError):
            IncompleteProcessor()  # type: ignore

    def test_hash_batch_is_abstract(self):
        """Test that hash_batch is an abstract method."""

        # Create a concrete class without implementing hash_batch
        class IncompleteProcessor(HashProcessor):
            def hash_first_1k(self, file):
                pass

            def hash_full_file(self, file):
                pass

        with pytest.raises(TypeError):
            IncompleteProcessor()  # type: ignore
