"""Load explicit repository packages without exposing the root import path."""
import importlib.machinery
import importlib.util
import pathlib
import runpy
import sys


class _SourceOnlyLoader(importlib.machinery.SourceFileLoader):
    """Compile repository source without reading or writing cached bytecode."""

    def get_code(self, fullname):
        return self.source_to_code(self.get_data(self.path), self.path)


class _RepositoryFinder:
    def __init__(self, root, names):
        self.root = root
        self.names = names

    def find_spec(self, fullname, path=None, target=None):
        name = fullname.split(".", 1)[0]
        if name not in self.names:
            return None
        specification = importlib.machinery.PathFinder.find_spec(fullname, path)
        if specification is None:
            return None
        boundary = self.root / name
        locations = specification.submodule_search_locations
        if locations is not None:
            for location in locations:
                resolved = pathlib.Path(location).resolve()
                if resolved != boundary and boundary not in resolved.parents:
                    raise ImportError("repository package outside approved boundary")
        if specification.origin is None and locations is not None:
            return specification
        source = pathlib.Path(specification.origin or "").resolve()
        if (not source.is_file() or source.suffix != ".py"
                or boundary not in source.parents):
            raise ImportError("repository modules require source inside approved boundary")
        specification.loader = _SourceOnlyLoader(fullname, str(source))
        return specification


def _load_package(root, name):
    boundary = root / name
    if boundary.resolve() != boundary:
        raise ImportError("repository package outside approved boundary")
    initializer = boundary / "__init__.py"
    if initializer.exists() and boundary not in initializer.resolve().parents:
        raise ImportError("repository package outside approved boundary")
    if initializer.is_file():
        specification = importlib.util.spec_from_file_location(
            name, initializer, loader=_SourceOnlyLoader(name, str(initializer)),
            submodule_search_locations=[str(root / name)])
        package = importlib.util.module_from_spec(specification)
        sys.modules[name] = package
        specification.loader.exec_module(package)
    else:
        specification = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
        specification.submodule_search_locations = [str(root / name)]
        package = importlib.util.module_from_spec(specification)
        sys.modules[name] = package


def main():
    root = pathlib.Path(sys.argv[1]).resolve()
    module = sys.argv[2]
    if not sys.flags.isolated or not (module.startswith("tools.") or module == "pytest"):
        raise SystemExit("isolated tools runtime required")
    sys.argv = [module] + sys.argv[3:]
    names = ("tools", "tests") if module == "pytest" else ("tools",)
    sys.meta_path.insert(0, _RepositoryFinder(root, names))
    for name in names:
        _load_package(root, name)
    runpy.run_module(module, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
