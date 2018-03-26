import os
import platform
from configparser import ConfigParser
from pathlib import Path

class Config:
    def __init__(self):
        self.user = {}
        self.workspace = {}

        self._load_user()
        self._load_workspace()

    def store(self):
        self._store_user()
        self._store_workspace()

    def __getitem__(self, key):
        combined = self.user.copy()
        combined.update(self.workspace)
        if key in combined:
            return combined[key]

    def __setitem__(self, key):
        pass

    def _load_user(self):
        config = ConfigParser()
        path = self._get_user_path()
        if path.is_file():
            with path.open() as config_file:
                config.read_file(config_file)
                self.user = dict(config['STAC'])
        else:
            self._store_user()

    def _load_workspace(self):
        pass

    def _generate_workspace(self):
        pass

    def _store_user(self):
        config = ConfigParser()
        config['STAC'] = self.user
        with self._get_user_path().open(mode='w') as config_file:
            config.write(config_file)

    def _store_workspace(self):
        # TODO: implement
        pass

    def _get_user_path(self):
        # TODO: handle MacOS
        if platform.system() == 'Windows':
            config_home = os.getenv('APPDATA')
            return Path('{}/stac.ini'.format(config_home))
        else:
            return Path('~/.stac').expanduser()


