import functools
import os.path

from .constants import HERE, COMMAND_MAPPING


class CacheProperty:
    def __init__(self, fget) -> None:
        self.fget = fget

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = self.fget(obj)
        setattr(obj, self.fget.__name__, value)
        return value


class HelpMenu:
    def __init__(self) -> None:
        with open(os.path.join(HERE, 'help_text.md'), 'r') as f:
            self._raw_menu = f.read()

    def get(self, subsection):
        if not subsection:
            full_menu = functools.reduce(lambda a, b: a.replace(b, ""), [self._raw_menu, "# ", "#", '`'])
            full_menu = full_menu.replace("\n- ", "\n")
            return print(full_menu)
        key = [k for k in self.cmd_docs if self.cmd_mapping_invert[subsection] in k][0]
        sub_docs = [
            functools.reduce(lambda a, b: a.replace(b, ""), [line, "#", '`']) 
            for line in self.cmd_docs[key]
        ]
        return print("\n".join(["", key, "=" * len(key), "", *sub_docs, ""]))
      
    @CacheProperty
    def menu(self):
        menu, key = {}, None
        lines = self._raw_menu.split('\n')
        for index, line in enumerate(lines):
            if set(line) == {"="}:
                key = lines[index - 1]
            elif key and line and set(lines[index + 1]) != {"="}:
                try:
                    menu[key].append(line)
                except KeyError:
                    menu[key] = [line]
        return menu
        
    @CacheProperty
    def cmd_docs(self):
        static_mode_docs = self.menu["static mode"]
        docs, key = {}, None
        for line in static_mode_docs:
            if line.startswith("### "):
                key = functools.reduce(lambda a, b: a.replace(b, ""), [line, "#", '`', ' ', '[', ']'])
            elif key:
                try:
                    docs[key].append(line)
                except KeyError:
                    docs[key] = [line]
        return docs
    
    @CacheProperty
    def cmd_mapping_invert(self):
        res = {}
        for key, values in COMMAND_MAPPING.items():
            res.update({value: key for value in values})
        return res

