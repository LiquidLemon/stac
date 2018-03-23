#!/usr/bin/env python3

# TODO : Dodać komentarz nagłówkowy

import os
from os import path
import sys

import logging
logging.captureWarnings(True)

import configparser
import getpass
import keyring

from bs4 import BeautifulSoup
from tabulate import tabulate

import stos


##### GENERAL HELPER FUNCTIONS #####
# TODO : Może zrobić to inaczej, nie globalną funkcją narzędziową?
def _fatal(message):
    print('fatal: ' + message, file=sys.stderr)
    sys.exit(1)

def _stac_path(repo_path):
    return path.join(repo_path, '.stac')

def _config_path(repo_path) :
    return path.join(_stac_path(repo_path), 'config')


##### CONFIGURATION #####
# TODO : Czy ogarnianie tego poprzez globalne funkcje jest ładne?
def _read_config(repo_path) :
    config = configparser.ConfigParser()
    try:
        with open(_config_path(repo_path)) as configfile :
            config.read_file(configfile)

    except FileNotFoundError:
        _fatal('Not a STAC workspace! Use `python stac.py init` first')

    return config

def _write_config(repo_path, config) :
    with open(_config_path(repo_path), 'w') as configfile :
        config.write(configfile)

def _get_credentials(repo_path, config) :
    stos_config = config['STAC']
    try :
        username = stos_config['username']
        password = keyring.get_password('stos', username)

    except KeyError:
        username = input('STOS username: ')
        password = getpass.getpass('STOS password: ')
        stos_config['username'] = username
        keyring.set_password('stos', username, password)
        _write_config(repo_path, config)

    return username, password


##### COMMAND HANDLERS #####
def init(repo_path) :
    # TODO : O ile dobrze pamiętam, ma być potem inny moduł do koniguracji
    os.makedirs(_stac_path(repo_path), exist_ok=True)
    with open(_config_path(repo_path), 'w') as configfile :
        config = configparser.ConfigParser()
        config['STAC'] = {}
        config.write(configfile)

def list_subjects(repo_path) :
    # TODO : Procedura konfiguracja-autoryzacja-sesja będzie się powtarzać
    config = _read_config(repo_path)
    username, password = _get_credentials(repo_path, config)
    sess = stos.Session(username, password)

    idx = 1
    rows = []
    for subject in sess.get_subjects() :
        rows.append([
            idx,
            subject.title,
            subject.id
        ])
        idx = idx + 1

    print(tabulate(rows, headers=['Nr', 'Przedmiot', 'ID']))
    print()
    print()

def list_problems(repo_path, sid) :
    # TODO : Procedura konfiguracja-autoryzacja-sesja będzie się powtarzać
    config = _read_config(repo_path)
    username, password = _get_credentials(repo_path, config)
    sess = stos.Session(username, password)
    
    for excercise in sess.get_excercises(stos.Subject(sid)) :
        print('» ' + excercise.title)
        print()

        rows = []
        for problem in excercise.problems :
            rows.append([
                problem.nr,
                problem.title,
                problem.id, 
                problem.result,
                problem.points,
                problem.deadline
            ])
        
        print(tabulate(rows, headers=[
            'Nr', 'Zadanie', 'ID', 'Wynik', 'Punkty', 'Termin']))
        print()
        print()

##### ENTRY POINT #####
if __name__ == '__main__':
    # TODO : Obsługa argumentów linii poleceń ma być upiększona później
    try:
        command = sys.argv[1]
        cwd = os.getcwd()
        if command == 'init':
            init(cwd)
        elif command == 'list':
            if sys.argv[2] == 'subjects':
                list_subjects(cwd)
            else :
                list_problems(cwd, int(sys.argv[2]))

    # TODO : Przechwytuje również błędy niezwiązane z linią poleceń
    except IndexError:
        print('usage: python stac.py <command> <args>', file=sys.stderr)
        print('example: python stac.py init          # zainicjalizuj przestrzeń roboczą', file=sys.stderr)
        print('example: python stac.py list subjects # wyświetl listę przedmiotów', file=sys.stderr)
        print('example: python stac.py list 365      # wyświetl zadania na przedmiot 365', file=sys.stderr)
        sys.exit(1)

    except requests.exceptions.ConnectionError:
        _fatal('Connection error!')
         # TODO : Ogarnąć, czy może moduł requests nie jest w stanie powiedzieć
         #      : nam czegoś więcej o tym, co poszło nie tak
