import json
import os.path

HERE = os.path.dirname(os.path.abspath(__file__))

# Changing this salt string will break compatibility
# with other vlt instances, and will break vlt's ability
# to decrypt data currently stored under this salt. 
# Unless you know what you're doing, best not to touch this.
TABLE_SALT = "»ûµQãDGïóê±PÊÚÐWò®Æ½¥ûdòjË¤Ó{Á½ÞÍÏ£ª¼ÙqÅç§EÎ¬õ¡"

class Settings:
    def __init__(self, prefix=None):
        self._name = (prefix + "_config.json" if prefix else "config.json")
        self._settings = self._init_config()

    def __getitem__(self, item):
        return self._settings.get(item, [])
    
    @property
    def name(self):
        return os.path.normpath(os.path.join(HERE, self._name))

    @property
    def settings(self):
        return self._settings

    @property
    def table_salt(self):
        return TABLE_SALT

    def archive(self, path):
        try:
            if path not in [archive for archive in self._settings["archives"].values()]:
                self._settings["archives"].update(
                    {str(max(int(x) for x in self._settings["archives"].keys()) + 1): path}
                )
        except KeyError:
            self._settings["archives"] = {"0": path}

    def update(self, obj):
        self._settings.update(obj)

    def _init_config(self):
        if not os.path.isfile(self.name):
            self._write(obj={"print_format": None})
        return self._read()

    def _read(self):
        with open(self.name, 'r') as f:
            return json.loads(f.read())

    def _write(self, obj=None):
        this = (self.settings if obj is None else obj)
        with open(self.name, "w") as f:
            f.write(json.dumps(this, indent=2, sort_keys=True))

