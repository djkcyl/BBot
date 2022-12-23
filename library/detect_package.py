import sys


def detect_package():
    try:
        if __nuitka_binary_dir is not None:  # type: ignore
            return "nuitka"
    except NameError:
        return (
            "pyinstaller"
            if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
            else False
        )
    return False


is_package = detect_package()
