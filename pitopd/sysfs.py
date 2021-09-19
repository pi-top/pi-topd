from os import listdir
from os.path import basename, isdir, isfile, join, realpath


class Node(object):
    __slots__ = ["_path_", "__dict__"]

    def __init__(self, path="/sys"):
        self._path_ = realpath(path)
        if not self._path_.startswith("/sys/") and not "/sys" == self._path_:
            raise RuntimeError("Using this on non-sysfs files is dangerous!")

        self.__dict__.update(dict.fromkeys(listdir(self._path_)))

    def __repr__(self):
        return '<sysfs.Node "%s">' % self._path_

    def __str__(self):
        return basename(self._path_)

    def __setattr__(self, name, val):
        if name.startswith("_"):
            return object.__setattr__(self, name, val)

        path = realpath(join(self._path_, name))
        if isfile(path):
            with open(path, "w") as fp:
                fp.write(val)
        else:
            raise RuntimeError("Cannot write to non-files.")

    def __getattribute__(self, name):
        if name.startswith("_"):
            return object.__getattribute__(self, name)

        path = realpath(join(self._path_, name))
        if isfile(path):
            with open(path, "r") as fp:
                return fp.read().strip()
        elif isdir(path):
            return Node(path)

    def __setitem__(self, name, val):
        return setattr(self, name, val)

    def __getitem__(self, name):
        return getattr(self, name)

    def __iter__(self):
        return iter(getattr(self, name) for name in listdir(self._path_))
