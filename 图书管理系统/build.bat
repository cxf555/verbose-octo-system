@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" > nul
cl /nologo /W3 /Fe:build\library_system.exe main.c book.c reader.c borrow.c stats.c utils.c
