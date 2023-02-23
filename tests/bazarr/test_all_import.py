#!/usr/bin/env python3

import ast
import os
from importlib.util import find_spec

import pytest

bazarr_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "bazarr")
libs_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "libs")


@pytest.mark.skip(reason="This test is not working yet")
def test_all_imports():
    for root, dirs, files in os.walk(bazarr_directory):
        for file in files:
            if file.endswith(".py"):
                modules = parse_imports(file=os.path.join(root, file))
                check_for_import(imported_modules=modules, path=root, file=file)


def parse_imports(file):
    with open(file, "r") as file:
        node = ast.parse(file.read())
    parsed_imports = [n.names[0].name for n in node.body if isinstance(n, ast.Import)]
    parsed_from_imports = [(n.module, [x.name for x in n.names], n.level) for n in node.body if
                           isinstance(n, ast.ImportFrom)]

    return parsed_imports + parsed_from_imports


def get_valid_module_path(path, module, level):
    module_file = os.path.sep.join(module.split("."))
    # if relative import
    if level:
        relative_path = path
        deep = level - 1
        for number in range(deep):
            relative_path = os.path.dirname(relative_path)
        if os.path.isfile(os.path.join(relative_path, module_file + ".py")):
            return os.path.join(relative_path, module_file + ".py")
        else:
            return os.path.join(relative_path, module_file, "__init__.py")
    # elif bazarr dir + module.py isfile
    elif os.path.isfile(os.path.join(bazarr_directory, module_file + ".py")):
        return os.path.join(bazarr_directory, module_file + ".py")
    # elif bazarr dir + module isdir
    elif os.path.isdir(os.path.join(bazarr_directory, module_file)):
        return os.path.join(bazarr_directory, module_file, "__init__.py")
    # elif libs dir + module.py isfile
    elif os.path.isfile(os.path.join(libs_directory, module_file + ".py")):
        return os.path.join(libs_directory, module_file + ".py")
    # elif libs dir + module isdir
    elif os.path.isdir(os.path.join(libs_directory, module_file)):
        return os.path.join(libs_directory, module_file, "__init__.py")
    # else base module
    else:
        return None


def check_for_import(imported_modules, path, file):
    print(os.path.join(path, file))
    for module in imported_modules:
        if module[1] == ["*"]:
            continue

        import_path = path
        if type(module) == str:
            module_name = module.strip()
            functions_name = []
            level = None
        else:
            try:
                module_name = module[0].strip()
            except AttributeError:
                continue
            functions_name = [x.strip() for x in module[1]]
            level = module[2]

        module_path = get_valid_module_path(import_path, module_name, level)

        if not module_path:
            try:
                find_spec(module_name)
                print("\tSUCCESS " + module_name)
                continue
            except Exception:
                print("\tFAILED " + module_name)
                raise ImportError
        else:
            # this is where we look into the included functions
            print("\t" + module_name + f" ({module_path})")
            with open(module_path, "r") as file:
                node = ast.parse(file.read())
            functions = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            classes = [n.name for n in node.body if isinstance(n, ast.ClassDef)]
            assignments = [n.id for n in ast.walk(node) if isinstance(n, ast.Name)]
            imports = [n.names[0].name for n in ast.walk(node) if isinstance(n, ast.Import)]
            imports_from = []
            for n in ast.walk(node):
                if isinstance(n, ast.ImportFrom):
                    imports_from += [x.name for x in n.names]

            for function in functions_name:
                if [x for x in (functions, classes, assignments, imports, imports_from) if function in x]:
                    print("\t\tSUCCESS", function)
                else:
                    print("\t\tFAILED", function)
                    raise ImportError
