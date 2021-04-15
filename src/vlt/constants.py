import os.path

HERE = os.path.dirname(os.path.abspath(__file__))
PRINT_FORMAT_SETTINGS = ['df', 'v', 'h']
TABLE_HEADERS = [' ', 'SOURCE', 'USERNAME', 'PASSWORD']
DEFAULT_PASSWORD_LENGTH = 42
MAX_PASSWORD_ITERATIONS = 500

COMMAND_MAPPING = {
    "add": ["-a", "+", "add"],
    "archive": ["-r", "archive"],
    "consume": ["-c", "consume"],
    "config": ["-cfg", "config"],
    "dump": ["-d", "dump"],
    "edit": ["-e", "edit"],
    "export": ["-x", "export"],
    "get": ["-g", "get"],
    "help": ["-h", "--help"],
    "link": ["-l", "link"],
    "build": ["-b", "build", "mk", "make"],
    "remove": ["rm", "-", "remove"],
    "reset": ["reset"],
    "ipython": ["ipython"]
}