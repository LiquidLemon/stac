#!/usr/bin/env python3
# TODO: Dodać komentarz nagłówkowy
import os
from os import path
import sys
import logging

import configparser
import getpass
import keyring
from bs4 import BeautifulSoup
from tabulate import tabulate
import requests
import click
from click import echo

import stos

logging.captureWarnings(True)


# GENERAL HELPER FUNCTIONS #
# TODO: Może zrobić to inaczej, nie globalną funkcją narzędziową?
def _fatal(message):
    echo('fatal: ' + message, err=True)
    sys.exit(1)


def _stac_path(repo_path):
    return path.join(repo_path, '.stac')


def _config_path(repo_path):
    return path.join(_stac_path(repo_path), 'config')


# CONFIGURATION #
# TODO: Czy ogarnianie tego poprzez globalne funkcje jest ładne?
def _read_config(repo_path):
    config = configparser.ConfigParser()
    try:
        with open(_config_path(repo_path)) as configfile:
            config.read_file(configfile)

    except FileNotFoundError:
        _fatal('Not a STAC workspace! Use `python stac.py init` first')

    return config


def _write_config(repo_path, config):
    with open(_config_path(repo_path), 'w') as configfile:
        config.write(configfile)


def _get_credentials(repo_path, config):
    stos_config = config['STAC']
    try:
        username = stos_config['username']
        password = keyring.get_password('stos', username)

    except KeyError:
        username = input('STOS username: ')
        password = getpass.getpass('STOS password: ')
        stos_config['username'] = username
        keyring.set_password('stos', username, password)
        _write_config(repo_path, config)

    return username, password


# COMMAND HANDLERS #
def list_subjects(repo_path):
    # TODO: Procedura konfiguracja-autoryzacja-sesja będzie się powtarzać
    config = _read_config(repo_path)
    username, password = _get_credentials(repo_path, config)
    sess = stos.Session(username, password)

    idx = 1
    rows = []
    for subject in sess.get_subjects():
        rows.append([
            idx,
            subject.title,
            subject.id
        ])
        idx = idx + 1

    echo(tabulate(rows, headers=['Nr', 'Przedmiot', 'ID']))
    echo()
    echo()


def list_problems(repo_path, sid):
    # TODO: Procedura konfiguracja-autoryzacja-sesja będzie się powtarzać
    config = _read_config(repo_path)
    username, password = _get_credentials(repo_path, config)
    sess = stos.Session(username, password)

    for excercise in sess.get_excercises(stos.Subject(sid)):
        echo('» ' + excercise.title)
        echo()

        rows = []
        for problem in excercise.problems:
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


CLICK_SETTINGS = {
    'help_option_names': ['-h', '--help']
}


@click.group(context_settings=CLICK_SETTINGS)
def cli():
    """Browse problems and submit solutions for the STOS platform.

    \b
    #define/***/ （ɺʘДʘ）ɺ/*2018*/long/**/int
    /**/#include  <stdio.h>/**STOS Client**/
    #define            ¯ا_/**/        return
    /*M*J*/           （ɺʘДʘ）ɺ        main()
    #define            ὢ/**/(         5/100)
    #define/*M**K*/    /**/_ا¯        ;;;};;
    {（ɺʘДʘ）ɺ/****/v   =8*4*2*        1;for(      （ɺʘДʘ）ɺ _ɩ_ɩ_
    =ὢ*ὢ*1;            _ɩ_ɩ_<5        ;_ɩ_ɩ_
    ++)putc            ((*&v+=        _ɩ_ɩ_%
    (-5+7)?            (_ɩ_ɩ_+        1)/2:-
    (7+8+4)*(_ɩ_ɩ_+21  -37-1+2        *2*2*2
    )),stdout-21/37+ὢ  );{;;};        {;;;;}

    ¯ا_(ὢ)_ا¯

    """
    pass


@cli.command()
@click.argument('path', default=os.getcwd())
def init(path):
    """Initialize the directory for use with stac."""
    # TODO: O ile dobrze pamiętam, ma być potem inny moduł do koniguracji
    os.makedirs(_stac_path(path), exist_ok=True)
    with open(_config_path(path), 'w') as configfile:
        config = configparser.ConfigParser()
        config['STAC'] = {}
        config.write(configfile)


@cli.command()
@click.argument('subject', required=False, type=click.INT)
def list(subject):
    """List subjects or exercises."""
    cwd = os.getcwd()
    try:
        if subject is None:
            list_subjects(cwd)
        else:
            list_problems(cwd, subject)
    except requests.exceptions.ConnectionError:
        # TODO: provide more information on failure
        _fatal('Connection error')


if __name__ == '__main__':
    cli()
