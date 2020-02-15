# (c) 2019-2020 KITAGAWA Yasutaka <kit494way@gmail.com>
#
# This file is part of Xavian.
#
# Xavian is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Xavian is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Xavian.  If not, see <https://www.gnu.org/licenses/>.

import json
import logging
import os
import time
import unicodedata
from datetime import datetime
from typing import Iterable, Union

import frontmatter
import pytz

import xapian

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Indexer(object):
    """Indexer."""

    extensions = (".md", ".rst", ".txt")

    def __init__(self, dbpath, *, cjk=False):
        """Initialize indexer with dbpath."""
        self._db = None
        self.dbpath = dbpath
        self.term_generator = xapian.TermGenerator()
        self.term_generator.set_stemmer(xapian.Stem("en"))

        if cjk:
            self.term_generator.set_flags(self.term_generator.FLAG_CJK_NGRAM)
            logger.info("FLAG_CJK_NGRAM enabled")
        self.open()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def open(self):
        if self._db is None:
            self._db = xapian.WritableDatabase(self.dbpath, xapian.DB_CREATE_OR_OPEN)
            logger.info("Open DB {}.".format(self.dbpath))
        else:
            logger.warn("DB {} is already opened.".format(self.dbpath))

        return self

    def close(self):
        if self._db is not None:
            self._db.close()
            self._db = None
            logger.info("Close DB {}.".format(self.dbpath))
        else:
            logger.warn("DB {} is already closed.".format(self.dbpath))

    def index_doc(self, doc, doc_id, metadata=None):
        """Index text.

        Args:
            doc (str): A string to index.
            doc_id (str): The id of `doc`.
            metadata (dict): Addtional data to index or display in search result.
        """
        xapian_doc = xapian.Document()
        self.term_generator.set_document(xapian_doc)
        norm_text = unicodedata.normalize("NFKC", doc)

        if metadata is None:
            metadata = {}

        if "title" in metadata:
            title = metadata["title"]
        else:
            lines = norm_text.splitlines()
            title = lines[0].strip("# ") if len(lines) else ""

        # without prefix for general search
        self.term_generator.index_text(norm_text)
        self.term_generator.increase_termpos()
        self.term_generator.index_text(title)

        if "tags" in metadata:
            self.term_generator.increase_termpos()
            self.term_generator.index_text(" ".join(metadata["tags"]))

        indexed_at = str(datetime.now(pytz.UTC))
        self.term_generator.index_text(indexed_at, 1, "XINDEXEDAT")

        # data for displaying search result
        data = {**metadata, "title": title, "indexed_at": indexed_at}
        xapian_doc.set_data(json.dumps(data))

        id_term = "Q" + doc_id
        xapian_doc.add_boolean_term(id_term)
        self._db.replace_document(id_term, xapian_doc)

        logger.info(
            "Index {}, id {}".format(
                metadata.get("path", title) if metadata else title, doc_id
            )
        )

    def index(self, path: Union[str, Iterable[str]]):
        """Index files."""
        if isinstance(path, str):
            if os.path.isfile(path):
                self.index_file(path)
            elif os.path.isdir(path):
                self.index_dir(path)
            else:
                logger.error("No such a file or directory.")
        elif iter(path):
            self.index_finder(path)
        else:
            logger.error("No such a file or directory.")
            raise TypeError("path must be path string or iterable.")

    def index_finder(self, finder: Iterable[str]):
        """Index files returned by finder.

        Args:
            finder: Iterable object which returns file paths.
        """
        processed_count = 0
        indexed_count = 0
        failed_count = 0
        for filepath in finder:
            processed_count += 1
            try:
                self.index_file(filepath)
                indexed_count += 1
            except Exception as e:
                logger.error(e)
                logger.warn("Error occured, skip {}".format(filepath))
                failed_count += 1

        logger.info(
            "Index files found by {}, processed {}, indexed {}, failed {}.".format(
                finder, processed_count, indexed_count, failed_count
            )
        )

    def index_file(self, path):
        """Index a file."""
        abspath = os.path.abspath(path)
        if path.endswith(".md"):
            self._index_markdown(abspath)
        else:
            self._index_text(abspath)

    def index_dir(self, directory):
        """Index files in the `directory` recursively.

        Ignore subdirectories starts with period.
        Ignore files not ends with any extensions in `self.extensions`.
        """
        with IndexTimestampLogger(directory) as timestamp_logger:
            self.index_finder(FileFinder(directory))

    def _index_markdown(self, filepath):
        doc_id = filepath
        with open(filepath, "r", encoding="utf-8") as fin:
            metadata = {"path": filepath}
            doc = frontmatter.load(fin)
            if "tags" in doc:
                metadata["tags"] = doc["tags"]
            self.index_doc(doc.content, doc_id, metadata)

    def _index_text(self, filepath):
        doc_id = filepath
        with open(filepath, "r", encoding="utf-8") as fin:
            metadata = {"path": filepath}
            self.index_doc(fin.read(), doc_id, metadata)


class IncrementalIndexer:
    """Index files modified or created after last indexing."""

    def __init__(self, dbpath, *, cjk: bool = False):
        self._indexer = Indexer(dbpath, cjk=cjk)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._indexer.close()

    def index(self, path: str):
        with IndexTimestampLogger(path) as timestamp_logger:
            index_path = os.path.abspath(path)
            finder = ModifiedFileFinder(index_path, timestamp_logger.last_timestamp)
            logger.info(
                "Index files that is updated after {}.".format(
                    timestamp_logger.last_timestamp
                )
            )
            self._indexer.index_finder(finder)


class IndexTimestampLogger:
    """Log index timestamp.

    Attributes:
        last_timestamp: The timestamp of index_path was indexed last time.
    """

    def __init__(self, index_path):
        self._index_path = os.path.abspath(index_path)
        self.last_timestamp: float = 0
        self._path_timestamp = {self._index_path: self.last_timestamp}
        self._timestamp_file = os.path.expanduser(
            "~/.config/xavian/index_timestamp.json"
        )

        if os.path.exists(self._timestamp_file):
            try:
                with open(self._timestamp_file, "r", encoding="utf8") as fin:
                    self._path_timestamp.update(json.load(fin))
            except Exception as e:
                logger.warning("Failed to load last indexed timestamp.")

        self.last_timestamp = self._path_timestamp[self._index_path]

    def __enter__(self):
        self._index_timestamp = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        with open(self._timestamp_file, "w", encoding="utf8") as fout:
            self._path_timestamp.update({self._index_path: self._index_timestamp})
            json.dump(self._path_timestamp, fout)


class FileFinder:
    """Iterable that contains indexable file paths in a directory."""

    extensions = (".md", ".rst", ".txt")

    def __init__(self, directory):
        self._directory = directory

    def __iter__(self):
        for dirpath, dirnames, filenames in os.walk(self._directory):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            yield from (
                os.path.join(dirpath, f)
                for f in filenames
                if any(map(f.endswith, self.extensions))
            )

    def __str__(self):
        return '{}("{}")'.format(self.__class__, self._directory)


class ModifiedFileFinder:
    """Iterable that contains modified indexable file paths in a directory.

    Iterator of ModifiedFileFinder(directory, timestamp) yield files modified
    after `timestamp`.
    """

    def __init__(self, directory: str, timestamp: float):
        self._finder = FileFinder(directory)
        self._timestamp = timestamp

    def __iter__(self):
        return (f for f in self._finder if os.path.getmtime(f) > self._timestamp)
