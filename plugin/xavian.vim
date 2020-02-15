" (c) 2019-2020 KITAGAWA Yasutaka <kit494way@gmail.com>
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

if exists("g:loaded_xavian")
  finish
endif
let g:loaded_xavian = 1

let s:sdir = expand("<sfile>:p:h:h")
let s:pypath = s:sdir . "/python"

python3 << EOD
import sys
import vim
sys.path.insert(0, vim.eval("s:pypath"))
EOD

command! -nargs=+ XavianSearch :call xavian#search(<f-args>)
command! -nargs=+ -complete=file XavianIndex :call xavian#index(<f-args>)
