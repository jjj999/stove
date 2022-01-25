import glob
import importlib
import os
import pathlib
import pkgutil
import typing as t


class working_at:

    def __init__(self, at: t.Union[str, pathlib.Path]) -> None:
        self._at = at
        self._current = os.getcwd()

    def __enter__(self) -> None:
        os.chdir(self._at)

    def __exit__(self, type, value, traceback) -> None:
        os.chdir(self._current)


def is_pkg_name(pkg_name: str) -> bool:
    try:
        pkg_name = __import__(pkg_name)
    except ImportError:
        return False
    else:
        path = getattr(pkg_name, "__path__", None)
        return path is not None


def is_pkg_path(pkg_path: str) -> bool:
    with working_at(pathlib.Path(pkg_path).parent):
        basename = os.path.basename(pkg_path)
        return is_pkg_name(basename)


def search_modules_from_name(
    pkg_name: str,
    recursive: bool = True,
) -> t.Tuple[str, ...]:
    pkg_name = __import__(pkg_name)
    path = getattr(pkg_name, "__path__", None)
    if path is None:
        raise ValueError(f"{pkg_name} is not a package.")

    modules = []
    for _, modname, is_pkg in pkgutil.iter_modules(path):
        modname = f"{pkg_name.__name__}.{modname}"
        if is_pkg:
            if recursive:
                modules.append(modname)
        else:
            modules.append(modname)

    return tuple(modules)


def search_modules_from_path(
    pkg_path: str,
    recursive: bool = True,
) -> t.Tuple[str, ...]:
    with working_at(pathlib.Path(pkg_path).parent):
        basename = os.path.basename(pkg_path)
        return search_modules_from_name(basename, recursive=recursive)


def import_all_modules(modules: t.Iterator[str]) -> None:
    for mod in modules:
        __import__(mod)


def import_all_modules_from_name(pkg_name: str) -> None:
    import_all_modules(search_modules_from_name(pkg_name))


def import_all_modules_from_path(pkg_path: str) -> t.Tuple[str]:
    paths = search_modules_from_path(pkg_path)
    with working_at(pathlib.Path(pkg_path).parent):
        import_all_modules(paths)


def reload_all_modules(modules: t.Iterator[str]) -> None:
    for mod in modules:
        mod = importlib.import_module(mod)
        importlib.reload(mod)


def reload_all_modules_from_name(pkg_name: str) -> None:
    reload_all_modules(search_modules_from_name(pkg_name))


def reload_all_modules_from_path(pkg_path: str) -> None:
    paths = search_modules_from_path(pkg_path)
    with working_at(pathlib.Path(pkg_path).parent):
        reload_all_modules(paths)


def search_pkgs_under(
    path: str,
    recursive: bool = True,
    ignores: t.Set[str] = set(),
) -> t.Tuple[str, ...]:
    pkgs = []

    def search_pkg_at(dir: str) -> None:
        pkgs_here = []
        for candidate in glob.glob(f"{dir}/*"):
            if os.path.isfile(candidate):
                continue
            basename = os.path.basename(candidate)
            if basename in ignores:
                continue
            if is_pkg_path(candidate):
                pkgs_here.append(candidate)
            if os.path.isdir(candidate) and recursive:
                search_pkg_at(candidate)

        pkgs.extend(pkgs_here)

    search_pkg_at(path)
    return tuple(pkgs)
