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

import logging
import os

import click

from . import index, search

logger = logging.getLogger("xavian")
logger.addHandler(logging.NullHandler())


@click.group()
@click.option("-v", "--verbose", count=True)
def cli(verbose):
    if verbose == 1:
        level = logging.INFO
    elif verbose > 1:
        level = logging.DEBUG

    if verbose > 0:
        FORMAT = "%(levelname)s:%(asctime)s:%(name)s:%(message)s"
        logging.basicConfig(level=level, format=FORMAT)


@click.command("index")
@click.argument("dbpath")
@click.argument("path")
@click.option("--cjk/--no-cjk", default=False)
@click.option("--increment/--no-increment", default=False)
def index_cmd(dbpath, path, cjk, increment):
    if increment:
        logger.info("Incremental indexing enabled.")
        indexer = index.IncrementalIndexer(dbpath, cjk=cjk)
    else:
        indexer = index.Indexer(dbpath, cjk=cjk)

    with indexer as idxer:
        idxer.index(path)


@click.command("search")
@click.argument("dbpath")
@click.argument("query")
@click.option("--cjk/--no-cjk", default=False)
def search_cmd(dbpath, query, cjk):
    with search.Searcher(dbpath, cjk=cjk) as searcher:
        for r in searcher.search(query):
            print(r)


cli.add_command(index_cmd)
cli.add_command(search_cmd)


if __name__ == "__main__":
    cli()
