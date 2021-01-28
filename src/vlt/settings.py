import json
import os.path

HERE = os.path.dirname(os.path.abspath(__file__))

class Settings:
    def __init__(self):
        self._settings = self._init_config()

    def __getattr__(self, attr):
        return self._settings.get(attr, [])

    @property
    def settings(self):
        return self._settings

    def update(self, obj):
        self._settings.update(obj)

    def archive(self, path):
        try:
            if path not in [archive for archive in self._settings["archives"].values()]:
                self._settings["archives"].update(
                    {str(max(int(x) for x in self._settings["archives"].keys()) + 1): path}
                )
        except KeyError:
            self._settings["archives"] = {"0": path}

    def _init_config(self):
        if not os.path.isfile(os.path.join(HERE, "config.json")):
            self._write(obj={})
        return self._read

    @property    
    def _read(self):
        with open(os.path.join(HERE, "config.json"), 'r') as f:
            return json.loads(f.read())

    def _write(self, obj=None):
        this = (self.settings if obj is None else obj)
        with open(os.path.join(HERE, "config.json"), "w") as f:
            f.write(json.dumps(this, indent=2, sort_keys=True))

