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
            win_ver = 'NT' + re.compile(r"\d+\.\d+").match(platform.win32_ver()[1]).group(0)
            self.user_agent += ' (Windows ' + win_ver + ')'
        elif platform.system() == 'Linux':
            lx_dist = platform.linux_distribution()[0] + ' ' \
            + platform.linux_distribution()[1]
            lx_ver = 'Linux ' + platform.release()
            self.user_agent += ' (' + lx_dist + '; ' + lx_ver + ')'

        r = self.__post({'p': 'login'}, {'login': username, 'password': password})
        if 'Wylogowanie' not in r.text:
            raise PermissionError('Login unsucessful')


    def get_subjects(self):
        resp = self.__get({'p': 'przedmioty'})
        soup = BeautifulSoup(resp.content)

        subjects = []
        patt_id = re.compile('id=(\d+)')
        for subject in soup.find('table').find_all('a') :
            subjects.append(Subject(
                title=subject.contents[0],
                id=int(re.search(patt_id, subject['href']).group(1))
            ))
        return subjects

    def get_excercises(self, subject):
        resp = self.__get({'p': 'viewprzedmiot', 'id': subject.id})
        soup = BeautifulSoup(resp.content)

        excercises = []
        excercise = Excercise('', [])
        patt_id = re.compile('id=(\d+)')
        patt_result = re.compile('>(\d+\.\d+%)<')
        for tr in soup.find('table').find_all('tr') :
            if tr['class'][0] == 'seprow' :
                if len(excercise.problems) :
                    excercises.append(Excercise(
                        excercise.title,
                        excercise.problems
                    ))
                    excercise.problems = []
                excercise.title = tr.td.span.contents[0]

            else :
                tds = tr.find_all('td')
                if len(tds) :
                    excercise.problems.append(Problem(
                        nr=int(tds[0].contents[0]),
                        title=tds[1].a.contents[0],
                        id=int(re.search(patt_id, tds[1].a['href']).group(1)),
                        result=tds[3].a.contents[0] if tds[3].a else '',
                        points=int(tds[4].contents[0]),
                        deadline=datetime.datetime.strptime(tds[5].contents[0], '%Y-%m-%d %H:%M:%S') if len(tds[5].contents) else None
                    ))
                    
        if len(excercise.problems) :
            excercises.append(excercise)
        
        return excercises


    def __get(self, params):
        return self.hts.get(broker_url,
                            params=params,
                            verify=False,
                            headers={'user-agent' : self.user_agent}
                            )

    def __post(self, params, data = None, files = None):
        return self.hts.post(broker_url,
                             params=params,
                             data=data,
                             files=files,
                             verify=False,
                             headers={'user-agent' : self.user_agent}
                             )


class Subject:
    title = ''
    id = 0

    def __init__(self, id, title = None):
        self.title = title
        self.id = id


class Excercise:
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
