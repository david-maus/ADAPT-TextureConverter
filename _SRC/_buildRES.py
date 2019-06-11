#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Resource (.qrc) to .py module

Works only with virtualEnv

by David Maus - www.david-maus.de

Written by David Maus / info@david-maus.de, 2018
"""
# fmt: off

# -------------------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------------------

import sys; sys.dont_write_bytecode = True
import os
import glob
import subprocess


# -------------------------------------------------------------------------------------
# Building
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------------------
# fmt: on


def main():

    if osPref == "LNX":
        pyrcc5Path = os.path.abspath(
            os.path.join(os.__file__, "../", "../", "../", "bin", "pyrcc5")
        )
    elif osPref == "WIN":
        pyrcc5Path = os.path.abspath(
            os.path.join(os.__file__, "../..", "Scripts", "pyrcc5.exe")
        )
    elif osPref == "OSX":
        pyrcc5Path = os.path.abspath(
            os.path.join(os.__file__, "../..", "bin", "pyrcc5")
        )

    for file in glob.glob(resourcesSource + "/*.qrc"):
        p = subprocess.Popen(
            pyrcc5Path + ' "' + file + '" -o "' + file.replace(".qrc", ".py") + '"',
            shell=True,
        )
        p.wait()


if __name__ == "__main__":

    if sys.platform == "linux" or sys.platform == "linux2":
        osPref = "LNX"

    elif sys.platform == "win32":
        osPref = "WIN"

    elif sys.platform == "darwin":
        osPref = "OSX"

    folderCurrent = os.path.abspath(os.path.dirname(__file__))
    resourcesSource = os.path.abspath(os.path.join(folderCurrent, uiDir))

    if sys.argv[1]:
        resourcesSource = sys.argv[1]
        resourcesSource = os.path.normpath(resourcesSource)
    main()
