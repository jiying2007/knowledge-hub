"""Load explicit repository packages without exposing the root import path."""
import importlib.machinery
import importlib.util
import pathlib
import runpy
import sys
import tempfile


def _load_package(root, name):
    initializer = root / name / "__init__.py"
    if initializer.is_file():
        specification = importlib.util.spec_from_file_location(
            name, initializer, submodule_search_locations=[str(root / name)])
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
    with tempfile.TemporaryDirectory(prefix="tools-bytecode-") as cache:
        sys.pycache_prefix = cache
        for name in (("tools", "tests") if module == "pytest" else ("tools",)):
            _load_package(root, name)
        runpy.run_module(module, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
