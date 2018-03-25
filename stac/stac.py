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
import colorama
import requests
import click
from click import echo

import stos

logging.captureWarnings(True)


# GENERAL HELPER FUNCTIONS #
# TODO: find another, probably better, way to report failures
def _fatal(message):
    echo('fatal: ' + message, err=True)
    sys.exit(1)


def _stac_path(repo_path):
    return path.join(repo_path, '.stac')


def _config_path(repo_path):
    return path.join(_stac_path(repo_path), 'config')


# CONFIGURATION #
# TODO: move configuration routines to another module
#       separate global and workspace settings
#       rebuild credentials storage routines
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
    # TODO: config-auth-session procedure WILL repeat in another commands
    config = _read_config(repo_path)
    username, password = _get_credentials(repo_path, config)
    sess = stos.Session(username, password)

    subjects = enumerate(sess.get_subjects(), start=1)
    rows = [[i, *subject.get_fields()] for i, subject in subjects]

    echo(tabulate(rows, headers=['Nr.', 'Subject', 'ID']))
    echo()
    echo()


def list_problems(repo_path, sid):
    # TODO: config-auth-session procedure WILL repeat in another commands
    config = _read_config(repo_path)
    username, password = _get_credentials(repo_path, config)
    sess = stos.Session(username, password)

    for exercise in sess.get_exercises(stos.Subject(sid)):
        echo(colorama.Style.BRIGHT + '» ' + exercise.title)
        echo(colorama.Style.RESET_ALL)

        rows = [problem.get_fields() for problem in exercise.problems]

        print(tabulate(rows, headers=[
            'Nr.', 'Problem title', 'ID', 'Result', 'Points', 'Deadline']))
        print()
        print()


CLICK_SETTINGS = {
    'help_option_names': ['-h', '--help']
}


@click.group(context_settings=CLICK_SETTINGS)
def cli():
    """Browse problems and submit solutions for the STOS platform.\033[1;37m

    \b
    #define/***/  ˂ɺʘДʘ˃ɺ/*2018*/long/\033[22;36m**/int\033[1;37m
    /**/#include  <stdio.h>/**STOS Cli\033[22;36ment**/\033[1;37m
    #define            ¯I_/**/        return
    /*F*F*/            ˂ɺʘДʘ˃ɺ        main()
    #define            ὢ/***/(        5/100)
    #define/*M**J*/    /**/_I¯        ;;;};;
    {˂ɺʘДʘ˃ɺ/*MK*/v    =8*4*2*        1;for(      \033[31m˂ɺʘДʘ˃ɺ _ɩ_ɩ_\033[37m
    =ὢ*ὢ*1;            _ɩ_ɩ_<5        ;_ɩ_ɩ_
    ++)putc            ((*&v+=        _ɩ_ɩ_%
    (-5+7)?            (_ɩ_ɩ_+        1)/2:-
    (7+8+4)*(_ɩ_ɩ_+21  -37-1+2        *2*2*2
    )),stdout-21/37+ὢ  );{;;};        {;;;;}

                      \033[32m¯I_(ὢ)_I¯\033[m

    """
    pass


@cli.command()
@click.argument('path', default=os.getcwd())
def init(path):
    """Initialize the directory as STAC workspace."""
    # TODO: rebuild configuration routines
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
    colorama.init(autoreset=True)
    cli()
