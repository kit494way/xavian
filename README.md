# Xavian

Xapian based full text search plugin for vim.

## Usage

### Index files

Curruntly supports .md, .rst, .txt files.

```vim
:XavianIndex /path/to/directory
```

This may take some time.

### Incremental index

With `--increment` option, you can index only files that is modified or created after last indexed time.

```vim
:XavianIndex --increment /path/to/directory
```

With `--no-increment`, index all files.

Default behavior of `:XavianIndex /path/to/directory` is changed by `g:xavian_incremental_index`.
If `g:xavian_incremental_index = 1`, `:XavianIndex /path/to/directory` execute incremental index.
Default, `:XavianIndex /path/to/directory` index all files.

### Search Files

```vim
:XavianSearch word
```

`XavianSearch` takes more than one word.
Max results is 20.

### CLI

There is a command line tool, bin/xavian .

## Install

First, install Xapian.
Then, install this plugin.

### Install Xapian

#### Download xapian source.

```sh
$ mkdir ~/src
$ cd ~/src
$ wget https://oligarchy.co.uk/xapian/1.4.13/xapian-core-1.4.13.tar.xz
$ wget https://oligarchy.co.uk/xapian/1.4.13/xapian-bindings-1.4.13.tar.xz
```

#### Make install xapian-core

```sh
$ tar xvf xapian-core-1.4.13.tar.xz
$ cd xapian-core-1.4.13/
$ mkdir ~/xapian-core-1.4.13 # Create a directory to install xapian-core.
$ ./configure --prefix=${HOME}/xapian-core-1.4.13
$ make -j 4
$ make install
```

#### Make install xapian-bindings

Create directories to install xapian-bindings

```sh
$ mkdir -p ~/xapian-bindings-1.4.13/python/3.6/{lib,install}
```

Install sphinx.
Spinx is required to build documents.

```sh
$ pip install sphinx
```

Make install xapian-bindings.

```sh
$ ./configure --with-python3 --prefix=${HOME}/xapian-bindings-1.4.13/python/3.6/install \
  XAPIAN_CONFIG=${HOME}/xapian-core-1.4.13/bin/xapian-config \
  PYTHON3=/usr/bin/python3.6 \ # Path to the python used by vim.
  PYTHON3_LIB=${HOME}/xapian-bindings-1.4.13/python/3.6/lib # Path to install xapian-binding for python
$ make -j 4
$ make install
```

Finally, make python to find xapian package.
For example, add additional.pth file to site-packages as follows.

```sh
$ echo ${HOME}/xapian-bindings-1.4.13/python/3.6/lib >> ${HOME}/.local/lib/python3.6/site-packages/additional.pth
```

### Install this plugin

Example to install by [dein.vim](https://github.com/Shougo/dein.vim).

```vim
call dein#add('kit494way/xavian')
```

Install python packages.
Make sure to install to python used by vim.

```sh
$ pip install -r requirements.txt
```

(Optional) If using CJK (Chinese, Japanese or Korean), set `let g:xavian_cjk = 1`.

## License

GNU General Public License v3.0

See [COPYING](COPYING) to see the full text.
