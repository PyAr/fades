@echo off

rem Copyright 2018 Facundo Batista, Nicolás Demarchi

if not [%*] == [] (
    set TARGET_TESTS="%*"
) else (
    set TARGET_TESTS=fades tests
)

bin\fades -r requirements.txt -x pytest -v -s %TARGET_TESTS%
