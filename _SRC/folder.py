import sys

sys.dont_write_bytecode = True
from pathlib import Path

sys.dont_write_bytecode = True


def rootDir(folder):
    """Root Path."""
    try:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent.joinpath(folder)
        else:
            return Path(__file__).resolve().parents[1].joinpath(folder)
    except Exception as e:
        return


def fileDir(folder):
    """Real file Path."""
    try:
        if getattr(sys, "frozen", False):
            return Path(sys._MEIPASS).resolve().joinpath(folder)
        else:
            return Path(__file__).resolve().parent.joinpath(folder)
    except Exception as e:
        return


def getFiles(folder, exFolders, exts, all=True):
    files = []
    pattern = "**/*"

    if all:
        pattern = "**/*"
    else:
        pattern = "*"

    for file in Path(folder).glob(pattern):
        directory = Path(file).parent
        filename = Path(file).stem
        extension = Path(file).suffix

        if Path(file).parent.name in exFolders:
            break

        if extension.lower() in exts:
            files.append(file)

    return files
