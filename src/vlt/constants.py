import os.path

HERE = os.path.dirname(os.path.abspath(__file__))
PRINT_FORMAT_SETTINGS = ['df', 'v', 'h']
TABLE_HEADERS = [' ', 'SOURCE', 'USERNAME', 'PASSWORD']
DEFAULT_PASSWORD_LENGTH = 42
MAX_PASSWORD_ITERATIONS = 500

COMMAND_MAPPING = {
    "add": ["-a", "+", "add"],
    "archive": ["-ar", "archive"],
    "consume": ["-c", "consume"],
    "dump": ["-d", "dump"],
    "edit": ["-e", "edit"],
    "export": ["-ex", "exp", "export"],
    "get": ["-g", "get"],
    "help": ["-h", "--help"],
    "link": ["-l", "lnk", "link"],
    "list": ["-ls", "ls", "list"],
    "make": ["-m", "mk", "make"],
    "remove": ["-rm", "rm", "-", "remove"],
    "reset": ["-rs", "reset"],
    "settings": ["-s", "set", "settings"],
    "ipython": ["ipython"]
}