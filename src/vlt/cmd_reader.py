import sys

def simple_isnan(item):
    try:
        float(item)
        return False
    except ValueError:
        return True

def reader():
    cmd = sys.argv[1]
    args = sys.argv[2::]
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