@echo off

rem Copyright 2014-2016 Facundo Batista, Nicolás Demarchi

if not [%*] == [] (
    set TARGET_TESTS="%*"
) else (
    set TARGET_TESTS=fades tests
)

bin\fades -r requirements.txt -x nosetests -v -s %TARGET_TESTS%
