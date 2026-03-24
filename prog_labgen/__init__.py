from .base_module import BaseTask, CLIParser  # noqa: F401


def __load_lab_modules() -> None:
    import importlib
    import inspect
    import os
    import sys

    cur_loc = __path__[0]
    current_module = sys.modules[__name__]

    for name in os.listdir(cur_loc):
        path = os.path.join(cur_loc, name)
        if name.startswith("lab") and os.path.isdir(path):
            module = importlib.import_module(f".{name}", "prog_labgen")
            for attr_name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseTask) and obj is not BaseTask:
                    setattr(current_module, attr_name, obj)
                elif isinstance(obj, CLIParser):
                    setattr(current_module, attr_name, obj)


__load_lab_modules()

__all__ = ["BaseTask", "CLIParser"]