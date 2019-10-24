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
import sys
import unicodedata

import xapian

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Searcher(object):
    def __init__(self, dbpath, *, cjk=False, page_size=20):
        self._db = None
        self.dbpath = dbpath
        self.cjk = cjk

        query_parser = xapian.QueryParser()
        query_parser.set_stemmer(xapian.Stem("en"))
        query_parser.set_default_op(xapian.Query.OP_AND)
        self.query_parser = query_parser

        self.query_parser_flag = (
            query_parser.FLAG_DEFAULT | query_parser.FLAG_CJK_NGRAM
            if self.cjk
            else query_parser.FLAG_DEFAULT
        )

        self.open()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def open(self):
        if self._db is None:
            self._db = xapian.Database(self.dbpath)
            logger.info("Open DB {}.".format(self.dbpath))
        else:
            logger.warn("DB {} is already opened.".format(self.dbpath))

        return self

    def close(self):
        if self._db is not None:
            self._db.close()
            logger.info("Close DB {}.".format(self.dbpath))
        else:
            logger.warn("DB {} is already closed.".format(self.dbpath))

    def search(self, query_string, offset=0, page_size=20):
        """Search documents by `query_string`.

        Args:
            query_string (str): Query string. Search words separated by white space.
            offset (int): Search result offset.
            page_size (int): Search result size.

        Returns:
            list(dict): Results of search.
        """
        enqire = xapian.Enquire(self._db)
        enqire.set_query(self.query(query_string))

        return [
            self._match_to_result(match) for match in enqire.get_mset(offset, page_size)
        ]

    def query(self, query_string):
        return self.query_parser.parse_query(
            unicodedata.normalize("NFKC", query_string), self.query_parser_flag
        )

    def _match_to_result(self, match):
        data = json.loads(match.document.get_data().decode("utf-8"))
        return {"title": "UNKNOWN", "rank": match.rank, **data}
