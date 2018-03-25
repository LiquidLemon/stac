# TODO: Dodać komentarz nagłówkowy

import requests
import platform
import re
import datetime

from bs4 import BeautifulSoup

broker_url = 'https://kaims.eti.pg.gda.pl/~kmocet/stos/index.php'


class Session:
    hts = []
    user_agent = 'STAC/0.1'

    def __init__(self, username, password):
        self.hts = requests.Session()

        if platform.system() == 'Windows':
            version_pattern = re.compile(r"\d+\.\d+")
            win_ver = version_pattern.match(platform.win32_ver()[1]).group(0)
            self.user_agent += ' (Windows NT' + win_ver + ')'

        elif platform.system() == 'Linux':
            lx_dist = platform.dist()[0] + ' ' + platform.dist()[1]
            lx_ver = 'Linux ' + platform.release()
            self.user_agent += ' (' + lx_dist + '; ' + lx_ver + ')'
        # TODO: macOS i FreeBSD

        params = {'login': username, 'password': password}
        r = self._post({'p': 'login'}, params)
        if 'Wylogowanie' not in r.text:
            raise PermissionError('Login unsucessful')

    def get_subjects(self):
        resp = self._get({'p': 'przedmioty'})
        soup = BeautifulSoup(resp.content)

        subjects = []
        patt_id = re.compile('id=(\d+)')
        for subject in soup.find('table').find_all('a'):
            subjects.append(Subject(
                title=subject.contents[0],
                id=int(re.search(patt_id, subject['href']).group(1))
            ))
        return subjects

    def get_exercises(self, subject):
        resp = self._get({'p': 'viewprzedmiot', 'id': subject.id})
        soup = BeautifulSoup(resp.content)

        exercises = []
        exercise = Exercise('', [])
        patt_id = re.compile('id=(\d+)')
        patt_result = re.compile('>(\d+\.\d+%)<')
        for tr in soup.find('table').find_all('tr'):
            if tr['class'][0] == 'seprow':
                if len(exercise.problems):
                    exercises.append(Exercise(
                        exercise.title,
                        exercise.problems
                    ))
                    exercise.problems = []
                exercise.title = tr.td.span.contents[0]

            else:
                tds = tr.find_all('td')
                if(len(tds) == 0):
                    continue

                if len(tds[5].contents) > 0:
                    deadline = datetime.datetime.strptime(
                        tds[5].contents[0], '%Y-%m-%d %H:%M:%S'
                    )
                else:
                    deadline = None

                if len(tds):
                    exercise.problems.append(Problem(
                        nr=int(tds[0].contents[0]),
                        title=tds[1].a.contents[0],
                        id=int(re.search(patt_id, tds[1].a['href']).group(1)),
                        result=tds[3].a.contents[0] if tds[3].a else '',
                        points=int(tds[4].contents[0]),
                        deadline=deadline
                    ))

        if len(exercise.problems):
            exercises.append(exercise)

        return exercises

    def _get(self, params):
        return self.hts.get(broker_url,
                            params=params,
                            verify=False,
                            headers={'user-agent': self.user_agent}
                            )

    def _post(self, params, data=None, files=None):
        return self.hts.post(broker_url,
                             params=params,
                             data=data,
                             files=files,
                             verify=False,
                             headers={'user-agent': self.user_agent}
                             )


class Subject:
    title = ''
    id = 0

    def __init__(self, id, title=None):
        self.title = title
        self.id = id


class Exercise:
    title = ''
    problems = []

    def __init__(self, title, problems):
        self.title = title
        self.problems = problems


class Problem:
    nr = 0
    title = ''
    id = 0
    result = ''
    points = 0
    deadline = []

    def __init__(self, nr, title, id, result, points, deadline):
        self.nr = nr
        self.title = title
        self.id = id
        self.result = result
        self.points = points
        self.deadline = deadline
