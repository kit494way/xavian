" (c) 2019, KITAGAWA Yasutaka <kit494way@gmail.com>
"
" This file is part of Xavian.
"
" Xavian is free software: you can redistribute it and/or modify
" it under the terms of the GNU General Public License as published by
" the Free Software Foundation, either version 3 of the License, or
" (at your option) any later version.
"
" Xavian is distributed in the hope that it will be useful,
" but WITHOUT ANY WARRANTY; without even the implied warranty of
" MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
" GNU General Public License for more details.
"
" You should have received a copy of the GNU General Public License
" along with Xavian.  If not, see <https://www.gnu.org/licenses/>.

let g:xavian_cjk = 0

function! xavian#search(...) abort
  let query = join(a:000)
python3 << EOD
import xavian
cjk = vim.eval("g:xavian_cjk") == 1
searcher = xavian.Searcher(vim.eval("s:xavian_dbpath()"), cjk=cjk)
results = searcher.search(vim.eval("query"))
paths = "\\n".join("{}:1:{}".format(result["path"], result["title"]) for result in results)
vim.command(":copen")
vim.command(':silent cgetexpr "{}"'.format(paths))
EOD
endfunction

function! xavian#index(...) abort
  if a:0
    let l:path = expand(a:1)
  else
    let l:path = expand("%:p")
  endif
python3 << EOD
import os
import vim
import xavian
cjk = vim.eval("g:xavian_cjk") == 1
indexer = xavian.Indexer(vim.eval("s:xavian_dbpath()"), cjk=cjk)
indexer.index(vim.eval("path"))
EOD
endfunction

function! s:xavian_dbpath() abort
  if exists("g:xavian_dbpath")
    return g:xavian_dbpath
  endif
  let xavin_dir = expand("~/.config/xavian")
  if !exists(xavin_dir)
    call mkdir(xavin_dir, "p")
  endif
  return xavin_dir . "/db"
endfunction
