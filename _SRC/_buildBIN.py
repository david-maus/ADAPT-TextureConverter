#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
PyInstaller Builder

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
import subprocess
import shutil

# -------------------------------------------------------------------------------------
# Global
# -------------------------------------------------------------------------------------

upxWIN      = "_thirdparty/upx394w"
upxLNX      = "_thirdparty/upx-3.94-amd64_linux"
upxOSX      = "_thirdparty/upx-3.94-amd64_linux"

# -------------------------------------------------------------------------------------
# Building
# -------------------------------------------------------------------------------------

def main():

    build(
        source="processHDR.py",
        name="_txConverter",
        binDir="../",
        oneFile=1,
        icon="ui/main.ico",
        uiDir="ui",
        add=[["./pyfiglet", "./pyfiglet"]],
        hiddenImport=["pyfiglet.fonts"],
        buildRES=0,
        upxWin=0,
        upxLnx=1,
        upxOsx=1,
        upxAfterWin=1,
        upxAfterLnx=1,
        upxAfterOsx=1,
        console=1,
        confirm=0,
        deleteSPEC=1,
        deleteTMP=1
    )


# -------------------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------------------
# fmt: on


def build(
    source,
    name,
    binDir,
    oneFile,
    icon,
    uiDir,
    add,
    hiddenImport,
    buildRES,
    upxWin,
    upxLnx,
    upxOsx,
    upxAfterWin,
    upxAfterLnx,
    upxAfterOsx,
    console,
    confirm,
    deleteSPEC,
    deleteTMP,
):

    folderCurrent = os.path.abspath(os.path.dirname(__file__))
    resourcesSource = os.path.abspath(os.path.join(folderCurrent, uiDir))

    name = name + "_" + osPref
    distPath = binDir + "/"
    workPath = "./_tmp/_pyinstallerWORK_" + osPref
    specPath = "./"

    if osPref == "WIN":

        upxDir = os.path.join(folderCurrent, upxWIN)
        upxCommand = (
            os.path.normpath(upxDir + "/upx.exe") + " --brute " + binDir + name + ".exe"
        )
        pyInstallerExe = os.path.abspath(
            os.path.join(os.__file__, "../", "../", "Scripts", "pyinstaller.exe")
        )
        if upxWin == 0:
            upx = " --noupx"
        else:
            upx = ""

    elif osPref == "LNX":

        upxDir = os.path.join(folderCurrent, upxLNX)
        upxCommand = (
            os.path.normpath(upxDir + "/upx") + " --brute " + binDir + name + ""
        )
        pyInstallerExe = os.path.abspath(
            os.path.join(os.__file__, "../", "../", "../", "bin", "pyinstaller")
        )
        if upxLnx == 0:
            upx = " --noupx"
        else:
            upx = ""

    elif osPref == "OSX":

        upxDir = os.path.join(folderCurrent, upxOSX)
        upxCommand = (
            os.path.normpath(upxDir + "/upx") + " --brute " + binDir + name + ""
        )
        pyInstallerExe = os.path.abspath(
            os.path.join(os.__file__, "../", "../", "bin", "pyinstaller")
        )
        if upxOsx == 0:
            upx = " --noupx"
        else:
            upx = ""

    if console == 0:
        console = " --noconsole"
    else:
        console = " --console"

    if confirm == 0:
        confirm = " --noconfirm"
    else:
        confirm = ""

    if oneFile:
        oneFileParameter = " -F "
    else:
        oneFileParameter = ""

    if buildRES:
        p = subprocess.Popen("python _buildRES.py " + resourcesSource, shell=True)
        p.wait()

    addData = []
    for data in add:
        dataSrc = data[0]
        dataDest = data[1]
        addData.append(" --add-data=" + dataSrc + os.pathsep + dataDest + " ")

    addImport = []
    for data in hiddenImport:
        addImport.append(" --hidden-import=" + data + " ")

    addImportStr = " ".join(addImport)
    addDataStr = " ".join(addData)

    runCommand = (
        pyInstallerExe
        + oneFileParameter
        + " --distpath "
        + distPath
        + " --workpath "
        + workPath
        + " --specpath "
        + specPath
        + ' --name "'
        + name
        + '" --icon "'
        + icon
        + '" --upx-dir '
        + str(upxDir)
        + upx
        + confirm
        + console
        + " --clean "
        + addImportStr
        + addDataStr
        + source
    )

    print(runCommand)

    p = subprocess.Popen(runCommand, shell=True)
    p.wait()

    print(upxCommand)

    if deleteSPEC:
        if os.path.isfile(name + ".spec"):
            os.remove(name + ".spec")
        else:
            print("Error: %s file not found" % (name + ".spec"))

    if deleteTMP:
        try:
            shutil.rmtree(os.path.join(folderCurrent, "_tmp"))
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))

    if upxAfterWin == 1 or upxAfterLnx == 1 or upxAfterOsx == 1:
        p = subprocess.Popen(upxCommand, shell=True)
        p.wait()


if __name__ == "__main__":

    if sys.platform == "linux" or sys.platform == "linux2":
        osPref = "LNX"

    elif sys.platform == "win32":
        osPref = "WIN"

    elif sys.platform == "darwin":
        osPref = "OSX"

    main()
