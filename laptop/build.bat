@echo off
pushd source

call vcvarsall x86_amd64
cl -wd4838 -Zi -Od -EHsc -Femerge main.cpp gdi32.lib
copy merge.exe "../build/merge.exe"
copy merge.pdb "../build/merge.pdb"
del *.obj *.pdb *.ilk *.exe

popd
pause
exit