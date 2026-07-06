@echo off

rem Copyright 2018 Facundo Batista, Nicolás Demarchi

if not [%*] == [] (
    set TARGET_TESTS="%*"
) else (
    set TARGET_TESTS=fades tests
)

python -m fades -r requirements.txt -x pytest -v %TARGET_TESTS%
