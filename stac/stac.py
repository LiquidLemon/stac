#!/usr/bin/env python3
# TODO: Dodać komentarz nagłówkowy
import os
from os import path
import sys
import logging

import keyring
from bs4 import BeautifulSoup
from tabulate import tabulate
import colorama
import requests
import click
from click import echo, prompt

import stos
from config import Config

config = Config()

logging.captureWarnings(True)

# GENERAL HELPER FUNCTIONS #
# TODO: find another, probably better, way to report failures
def _fatal(message):
    echo('fatal: ' + message, err=True)
    sys.exit(1)


# CONFIGURATION #

def get_credentials():
    username = config['username']
    if username is None:
        username = prompt('STOS username')
        # TODO: save where it was read from
        config.user['username'] = username
        config.store()

    password = keyring.get_password('stos', username)
    if password is None:
        password = prompt('STOS password', hide_input=True)
        keyring.set_password('stos', username, password)

    return username, password


# COMMAND HANDLERS #
def list_subjects():
    # TODO: config-auth-session procedure WILL repeat in another commands
    username, password = get_credentials()
    sess = stos.Session(username, password)

    subjects = enumerate(sess.get_subjects(), start=1)
    rows = [[i, *subject.get_fields()] for i, subject in subjects]

    echo(tabulate(rows, headers=['Nr.', 'Subject', 'ID']))
    echo()
    echo()


def list_problems(sid):
    # TODO: config-auth-session procedure WILL repeat in another commands
    username, password = get_credentials()
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
    pass

@cli.command()
@click.argument('subject', required=False, type=click.INT)
def list(subject):
    """List subjects or exercises."""
    try:
        if subject is None:
            list_subjects()
        else:
            list_problems(subject)

    except requests.exceptions.ConnectionError:
        # TODO: provide more information on failure
        _fatal('Connection error')


if __name__ == '__main__':
    colorama.init(autoreset=True)
    cli()
