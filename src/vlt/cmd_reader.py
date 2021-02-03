import sys

from .help_menu import HelpMenu

def simple_isnan(item):
    try:
        float(item)
        return False
    except ValueError:
        return True

def _get_help(cmd=""):
    help_menu = HelpMenu()
    help_menu.get(cmd)
    sys.exit()

def reader():
    cmd = sys.argv[1]
    args = sys.argv[2::]
    if cmd in ("-h", "--help"):
        return _get_help()
    elif any(h in args for h in ("-h", "--help")):
        return _get_help(cmd)
    kwargs = {}
    kwarg_keys = reversed([
        index for index, item in enumerate(args) 
        if (item.startswith('-') and simple_isnan(item))
    ])
    for k in kwarg_keys:
        value = args.pop(k+1)
        key = args.pop(k)
        kwargs[key] = value

    return cmd, args, kwargs