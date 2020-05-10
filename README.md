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

You can use [this](https://github.com/kit494way/xapian-installer) to install.

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
