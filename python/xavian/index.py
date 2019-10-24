# (c) 2019, KITAGAWA Yasutaka <kit494way@gmail.com>
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
import unicodedata
from datetime import datetime

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

    def index(self, path):
        """Index files.

        Args:
            path (str): Path to a file or directory.
        """
        if os.path.isfile(path):
            self.index_file(path)
        elif os.path.isdir(path):
            self.index_dir(path)
        else:
            logger.error("No such a file or directory.")

    def index_file(self, path):
        """Index a file."""
        self._index_file_abspath(os.path.abspath(path))

    def index_dir(self, directory):
        """Index files in the `directory` recursively.

        Ignore subdirectories starts with period.
        Ignore files not ends with any extensions in `self.extensions`.
        """
        processed_count = 0
        indexed_count = 0
        failed_count = 0
        for filepath in self._walk(directory):
            processed_count += 1
            try:
                self._index_file_abspath(filepath)
                indexed_count += 1
            except Exception as e:
                logger.error(e)
                logger.warn("Error occured, skip {}".format(filepath))
                failed_count += 1

        logger.info(
            "Index directory {}, processed {}, indexed {}, failed {}.".format(
                directory, processed_count, indexed_count, failed_count
            )
        )

    def _walk(self, directory):
        for dirpath, dirnames, filenames in os.walk(directory):
            dirnames = [d for d in dirnames if not d.startswith(".")]
            yield from (
                os.path.join(dirpath, f)
                for f in filenames
                if any(map(f.endswith, self.extensions))
            )

    def _index_file_abspath(self, filepath):
        if filepath.endswith(".md"):
            self._index_markdown(filepath)
        else:
            self._index_text(filepath)

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
