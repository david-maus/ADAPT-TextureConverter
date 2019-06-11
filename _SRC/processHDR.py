#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
ADAPT LOOKDEV - Texture Converter

by David Maus - www.david-maus.de


Copyright (C) David Maus - All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Written by David Maus / info@david-maus.de, 2018
"""
# fmt: off

# -------------------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------------------
import sys; sys.dont_write_bytecode = True
import os
import time
import Queue
import threading
from tqdm import tqdm, trange
from tqdm._utils import _term_move_up
from colorama import init, Fore, Back, Style
init(
    strip=not sys.stdout.isatty(), autoreset=True
)  # strip colors if stdout is redirected
from termcolor import cprint
from pyfiglet import figlet_format
import OpenImageIO as oiio
from OpenImageIO import ImageInput, ImageOutput
from OpenImageIO import ImageBuf, ImageSpec, ImageBufAlgo
from pathlib import Path
import shlex
import struct
import platform
import subprocess
import folder
import argparse
from argparse import RawTextHelpFormatter
# import win_unicode_console

# win_unicode_console.enable()


# -------------------------------------------------------------------------------------
# Global
# -------------------------------------------------------------------------------------

__author__      = "David Maus"
__website__     = "www.david-maus.de"
__version__     = "0.2.0"
__license__     = ""
__title__       = "ADAPT LOOKDEV"
__subTitle__    = "Texture Converter " + __version__ + u" | (c) 2018 - " + __website__
__desc__        = "tiled/mipmapped EXR from textures/hdrs - Build with OpenImageIO"

# -------------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------------

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# -------------------------------------------------------------------------------------
# Global vars
# -------------------------------------------------------------------------------------

tiledPrefix         = "-tiled"
blurredPrefix       = "-blurred"
mipmapPrefix        = "-mipmap"

hdrExtension        = ".exr"
mipmapExtension     = ".tx"
thumbnailExtension  = ".jpg"

thumbnailWidth      = 270
hdrWidth            = 8192
hdrBlurWidth        = 4096

tileSize            = 64

blurAmountX         = 25.0
blurAmountY         = 35.0
blurFilter          = "bspline"
resizeFilter        = "mitchell"

errorFlag           = 0
threadResult        = Queue.Queue()
prefix              = _term_move_up() + '\r'
barFormat           = "{desc:<9}{percentage:3.0f}%|{bar}| {n_fmt:<4}/{total_fmt:<4} {elapsed}<{remaining:<6}, {rate_fmt:<11}{postfix}"

textureExts         = [".jpg", ".exr", ".tif", ".jpeg", ".hdr", ".png"]
hdrExts             = [".exr", ".hdr"]
hdrPrevExts         = [".jpg"]
# excludeFolders      = ["_ADAPTLOOKDEV_", "_SRC"]

# -------------------------------------------------------------------------------------
# Get & Set Pathes
# -------------------------------------------------------------------------------------


rootFolder          = folder.rootDir("")
adaptFolder         = folder.rootDir("_ADAPTLOOKDEV_")
hdrFolder           = folder.rootDir("_ADAPTLOOKDEV_/lighting/hdr")
hdrPrevFolder       = folder.rootDir("_ADAPTLOOKDEV_/lighting/hdr/previews")
hdrBlurFolder       = folder.rootDir("_ADAPTLOOKDEV_/lighting/hdr/blurred")

# uiFilePath          = folder.fileDir("ui/interface.ui")


# -------------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------------
# fmt: on


__func = None


def get_terminal_size():
    if __func is None:
        return _get_terminal_size()
    else:
        return __func()


def _get_terminal_size():
    """ getTerminalSize()
     - get width and height of console
     - works on linux,os x,windows,cygwin(windows)
     originally retrieved from:
     http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    """
    global __func
    current_os = platform.system()
    tuple_xy = None
    if current_os == "Windows":
        tuple_xy = _get_terminal_size_windows()
        if tuple_xy is None:
            tuple_xy = _get_terminal_size_tput()
            __func = tuple_xy
            # needed for window's python in cygwin's xterm!
        else:
            __func = tuple_xy
    if current_os in ["Linux", "Darwin"] or current_os.startswith("CYGWIN"):
        tuple_xy = _get_terminal_size_linux()
    if tuple_xy is None:
        #        print("default")
        tuple_xy = _default()  # default value
        __func = tuple_xy
    elif __func is None:
        __func = _get_terminal_size_linux()
    return tuple_xy


def _default():
    return (80, 25)


def _get_terminal_size_windows():
    try:
        if __func is None:
            global ctypes
            import ctypes
        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = ctypes.windll.kernel32.GetStdHandle(-12)
        csbi = ctypes.create_string_buffer(22)
        res = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (
                bufx,
                bufy,
                curx,
                cury,
                wattr,
                left,
                top,
                right,
                bottom,
                maxx,
                maxy,
            ) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
            return sizex, sizey
    except:
        pass


def _get_terminal_size_tput():
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
        cols = int(subprocess.check_output(shlex.split("tput cols")))
        rows = int(subprocess.check_output(shlex.split("tput lines")))
        return (cols, rows)
    except:
        pass


def _get_terminal_size_linux():
    def ioctl_GWINSZ(fd):
        try:
            if __func is None:
                global fcntl, termios
                import fcntl
                import termios
            cr = struct.unpack("hh", fcntl.ioctl(fd, termios.TIOCGWINSZ, "1234"))
            return cr
        except:
            pass

    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except Exception as err:
            print(str(err))
    if not cr:
        try:
            cr = (os.environ["LINES"], os.environ["COLUMNS"])
        except:
            return None
    return int(cr[1]), int(cr[0])


def clearTerminal():
    # os.system("cls||clear")

    command = "cls" if platform.system().lower() == "windows" else "clear"
    os.system(command)
    # tqdm.write("\n" * getTerminalSize()[0])


def wait_key():
    """Wait for a key press on the console and return it."""
    result = None
    if os.name == "nt":
        import msvcrt

        result = msvcrt.getch()
    else:
        import termios

        fd = sys.stdin.fileno()

        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        try:
            result = sys.stdin.read(1)
        except IOError:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)

    return result


def showUI(title, content):
    clearTerminal()

    cprint(
        figlet_format(__title__, font="3-d", justify="center", width=width).center(
            width
        ),
        "red",
        attrs=["bold"],
    )
    cprint((__subTitle__).center(width), "green")
    cprint((__desc__).center(width), "red")
    cprint(("-" * width).center(width), "red")
    # cprint("\n".center(width), "red")
    cprint((title).center(width), "grey", "on_white")
    cprint((content).center(width), "grey", "on_white")
    tqdm.write(prefix + "\n")


def threadAndStatus(targetFunc, args, name, id, result):
    if len(args) == 0:

        t1 = threading.Thread(target=targetFunc, args=[args])
    else:
        t1 = threading.Thread(target=targetFunc, args=(args))

    t1.start()

    pbar = tqdm(
        total=100,
        ncols=width,
        leave=True,
        position=id,
        desc=name,
        ascii=True,
        bar_format=barFormat,
    )
    while t1.is_alive() and errorFlag == 0:
        pbar.update(0.1)
        time.sleep(0.5)
    t1.join()
    pbar.n = 100
    pbar.refresh()
    pbar.close()
    if result is True:
        return threadResult.get()
    else:
        True


def calculateResizeHeight(origWidth, origHeight, newWidth):
    newHeight = int(round(float(origHeight) / origWidth * newWidth))

    return newHeight


def convertColor(srcBuffer, fromColor="linear", toColor="sRGB"):
    Dst = ImageBuf()
    ImageBufAlgo.colorconvert(Dst, srcBuffer, fromColor, toColor)
    threadResult.put(Dst)
    return Dst


def resizeHDR(scrBuffer, width, height):
    srcSpec = scrBuffer.spec()

    resizedBuffer = ImageBuf(
        ImageSpec(width, height, srcSpec.nchannels, srcSpec.format)
    )
    ImageBufAlgo.resize(resizedBuffer, scrBuffer, filtername=resizeFilter)
    threadResult.put(resizedBuffer)
    return resizedBuffer


def writeJPG(scrBuffer, outFile):
    global errorFlag

    try:
        scrBuffer.specmod().attribute("quality", 80)
        scrBuffer.write(outFile)

        errorFlag = 0

    except Exception as e:
        errorFlag = 1

        tqdm.write(
            prefix
            + Fore.RED
            + "Error on conversion. Maybe wrong/corrupt .hdr file or resolution too high (over 8192)."
        )


def writeEXR(scrBuffer, outFile):
    global errorFlag

    try:

        config = ImageSpec()
        # config.attribute("maketx:highlightcomp", 1)
        config.attribute("maketx:filtername", "lanczos3")
        config.attribute("maketx:opaquedetect", 1)
        config.attribute("maketx:oiio options", 1)

        scrBuffer.set_write_tiles(tileSize, tileSize)

        ImageBufAlgo.make_texture(oiio.MakeTxEnvLatl, scrBuffer, outFile, config)

        errorFlag = 0

    except Exception as e:
        errorFlag = 1

        tqdm.write(
            prefix
            + Fore.RED
            + "Error on conversion. Maybe wrong/corrupt .hdr file or resolution too high (over 8192)."
        )


def writeTexture(scrBuffer, outFile):
    global errorFlag

    try:

        config = ImageSpec()
        # config.attribute("maketx:highlightcomp", 1)
        config.attribute("maketx:filtername", "lanczos3")
        # config.attribute("maketx:opaquedetect", 1)
        config.attribute("maketx:oiio options", 1)

        scrBuffer.set_write_tiles(tileSize, tileSize)

        ImageBufAlgo.make_texture(oiio.MakeTxTexture, scrBuffer, outFile, config)

        errorFlag = 0

    except Exception as e:
        errorFlag = 1

        tqdm.write(
            prefix
            + Fore.RED
            + "Error on conversion. Maybe wrong/corrupt texture file or resolution too high."
        )


def blurImage(srcBuffer):
    K = ImageBuf()
    ImageBufAlgo.make_kernel(K, blurFilter, blurAmountX, blurAmountY)
    Blurred = ImageBuf()
    ImageBufAlgo.convolve(Blurred, srcBuffer, K)

    threadResult.put(Blurred)
    return Blurred


# -------------------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------------------


def processHDRs():
    """Main entry point of the app."""

    if not Path(hdrPrevFolder).exists():
        Path(hdrPrevFolder).mkdir(parents=True)
    if not Path(hdrBlurFolder).exists():
        Path(hdrBlurFolder).mkdir(parents=True)

    hdrFiles = folder.getFiles(hdrFolder, "", hdrExts, all=False)
    previewFiles = folder.getFiles(hdrPrevFolder, "", hdrPrevExts, all=False)

    hdrFilesTiling = []
    hdrFilesBlurring = []
    hdrFilesPreview = []

    hdrFilesPreviewNames = []

    for previewFile in previewFiles:

        directory = Path(previewFile).parent
        filename = Path(previewFile).stem
        extension = Path(previewFile).suffix

        hdrFilesPreviewNames.append(filename)

    for hdrFile in hdrFiles:

        directory = Path(hdrFile).parent
        filename = Path(hdrFile).stem
        extension = Path(hdrFile).suffix

        IMG_CACHE = oiio.ImageCache.create(True)

        frameBufferOrig = ImageBuf(str(hdrFile))
        spec = frameBufferOrig.spec()

        if blurredPrefix not in filename:
            if Path(hdrBlurFolder, filename + blurredPrefix + hdrExtension).exists():
                pass
            else:
                hdrFilesBlurring.append(hdrFile)
        if (
            spec.tile_width == spec.width
            or spec.tile_width == 0
            or frameBufferOrig.nmiplevels == 1
        ):
            hdrFilesTiling.append(hdrFile)
        if filename not in hdrFilesPreviewNames:
            hdrFilesPreview.append(hdrFile)

        IMG_CACHE.invalidate(str(hdrFile))

    if (
        len(hdrFilesBlurring) == 0
        and len(hdrFilesTiling) == 0
        and len(hdrFilesPreview) == 0
    ):

        showUI("", "Nothing to do...")

    if len(hdrFilesTiling) is not 0:

        showUI(
            "Searching for Files",
            "Found "
            + str(len(hdrFilesTiling))
            + " files in scanline/No MipMap or not .exr format. We will make some :)",
        )
        time.sleep(4)

        for hdrFileTiling in tqdm(
            hdrFilesTiling,
            desc="Complete",
            ncols=width,
            position=2,
            unit="file",
            ascii=True,
            bar_format=barFormat,
        ):

            directory = Path(hdrFileTiling).parent
            filename = Path(hdrFileTiling).stem
            extension = Path(hdrFileTiling).suffix

            showUI(
                "Make tiled / MipMapped .exr", "Current File: " + filename + extension
            )

            IMG_CACHE = oiio.ImageCache.create(True)

            frameBufferOrig2 = ImageBuf(str(hdrFileTiling))
            spec2 = frameBufferOrig2.spec()

            outPutFile = str(Path(directory, filename + tiledPrefix + hdrExtension))

            if spec2.width > hdrWidth:

                newHeight = calculateResizeHeight(spec2.width, spec2.height, hdrWidth)
                resizedFramebuffer = threadAndStatus(
                    resizeHDR,
                    [frameBufferOrig2, hdrWidth, newHeight],
                    "Resizing",
                    1,
                    True,
                )

                writeFramebuffer = threadAndStatus(
                    writeEXR, [resizedFramebuffer, outPutFile], "Saving", 0, False
                )

            else:
                writeFramebuffer = threadAndStatus(
                    writeEXR, [frameBufferOrig2, outPutFile], "Saving", 0, False
                )

            IMG_CACHE.invalidate(str(hdrFileTiling))

            # if Path(hdrFileTiling).exists():
            #     Path(hdrFileTiling).unlink()
            #     Path(hdrFileTiling).with_suffix(hdrExtension)
            #     Path(outPutFile).rename(hdrFileTiling)

            if errorFlag == 0:
                # If file exists, delete it
                if Path(hdrFileTiling).exists():
                    newFile = Path(hdrFileTiling).with_suffix(hdrExtension)
                    Path(hdrFileTiling).unlink()
                    Path(outPutFile).resolve().rename(newFile)

                    if hdrFileTiling in hdrFilesPreview:
                        hdrFilesPreview.remove(hdrFileTiling)
                        hdrFilesPreview.append(newFile)
                    if hdrFileTiling in hdrFilesBlurring:
                        hdrFilesBlurring.remove(hdrFileTiling)
                        hdrFilesBlurring.append(newFile)
                    tqdm.write(
                        prefix + Fore.GREEN + "Successfully replaced the original file."
                    )

                else:
                    tqdm.write(
                        prefix
                        + Fore.RED
                        + "Error: %s not found. Could not delete the File."
                        % hdrFileTiling
                    )

            else:
                tqdm.write(
                    prefix
                    + Fore.RED
                    + "Something went wrong on conversion. File not deleted."
                )

        showUI("", Fore.GREEN + "All HDRs converted...")

    if len(hdrFilesBlurring) is not 0:

        showUI(
            __title__,
            "Found "
            + str(len(hdrFilesBlurring))
            + " files with no blurred partners. We will make some :)",
        )
        time.sleep(4)

        for hdrFileBlurring in tqdm(
            hdrFilesBlurring,
            desc="Complete",
            ncols=width,
            position=3,
            unit="file",
            ascii=True,
            bar_format=barFormat,
        ):

            directory = Path(hdrFileBlurring).parent
            filename = Path(hdrFileBlurring).stem
            extension = Path(hdrFileBlurring).suffix

            showUI("Blurring HDRs", "Current File: " + filename + extension)

            IMG_CACHE = oiio.ImageCache.create(True)

            frameBufferOrig2 = ImageBuf(str(hdrFileBlurring))
            spec2 = frameBufferOrig2.spec()

            outPutFile = str(
                Path(hdrBlurFolder, filename + blurredPrefix + hdrExtension)
            )

            newHeight = calculateResizeHeight(spec2.width, spec2.height, hdrBlurWidth)

            resizedFramebuffer = threadAndStatus(
                resizeHDR,
                [frameBufferOrig2, hdrBlurWidth, newHeight],
                "Resizing",
                2,
                True,
            )
            blurredFramebuffer = threadAndStatus(
                blurImage, [resizedFramebuffer], "Blurring", 1, True
            )
            writeFramebuffer = threadAndStatus(
                writeEXR, [blurredFramebuffer, outPutFile], "Saving", 0, False
            )

            IMG_CACHE.invalidate(str(hdrFileBlurring))

            # hdrFilesPreview.append(outPutFile)

        showUI("", Fore.GREEN + "All HDRs blurred...")

    if len(hdrFilesPreview) is not 0:

        showUI(
            "Searching for Files",
            "Found "
            + str(len(hdrFilesPreview))
            + " files with no Preview-JPGs. We will make some :)",
        )
        time.sleep(4)

        for hdrFilePreview in tqdm(
            hdrFilesPreview,
            desc="Complete",
            ncols=width,
            position=3,
            unit="file",
            ascii=True,
            bar_format=barFormat,
        ):

            directory = Path(hdrFilePreview).parent
            filename = Path(hdrFilePreview).stem
            extension = Path(hdrFilePreview).suffix

            showUI("Thumbnail creation", "Current File: " + filename + extension)

            IMG_CACHE = oiio.ImageCache.create(True)

            frameBufferOrig2 = ImageBuf(str(hdrFilePreview))
            spec2 = frameBufferOrig2.spec()

            outPutFile = str(Path(hdrPrevFolder, filename + thumbnailExtension))

            sRGBBuffer = threadAndStatus(
                convertColor, [frameBufferOrig2, "linear", "sRGB"], "Lin2sRGB", 2, True
            )

            newHeight = calculateResizeHeight(spec2.width, spec2.height, thumbnailWidth)

            resizedFramebuffer = threadAndStatus(
                resizeHDR, [sRGBBuffer, thumbnailWidth, newHeight], "Resizing", 1, True
            )
            writeFramebuffer = threadAndStatus(
                writeJPG, [resizedFramebuffer, outPutFile], "Saving", 0, False
            )

            IMG_CACHE.invalidate(str(hdrFilePreview))

        showUI("", Fore.GREEN + "All previews generated...")

    tqdm.write(prefix + "Press Enter to exit or close the Terminal")
    wait_key()


def processTextures(excludeFolders):
    allTextures = folder.getFiles(rootFolder, excludeFolders, textureExts, all=True)
    selectedTextures = []

    for texture in allTextures:

        directory = Path(texture).parent
        filename = Path(texture).stem
        extension = Path(texture).suffix

        IMG_CACHE = oiio.ImageCache.create(True)

        frameBufferOrig = ImageBuf(str(texture))
        spec = frameBufferOrig.spec()

        if (
            spec.tile_width == spec.width
            or spec.tile_width == 0
            or frameBufferOrig.nmiplevels == 1
        ):
            if Path(directory, filename + mipmapPrefix + mipmapExtension).exists():
                pass
            else:
                selectedTextures.append(texture)

        IMG_CACHE.invalidate(str(texture))

    if len(selectedTextures) == 0:

        showUI("", "Nothing to do...")

    if len(selectedTextures) is not 0:

        showUI(
            "Searching for Files",
            "Found "
            + str(len(selectedTextures))
            + " files in scanline/No MipMap or not .exr format. We will make some :)",
        )
        time.sleep(4)

        for texture in tqdm(
            selectedTextures,
            desc="Complete",
            ncols=width,
            position=1,
            unit="file",
            ascii=True,
            bar_format=barFormat,
        ):

            directory = Path(texture).parent
            filename = Path(texture).stem
            extension = Path(texture).suffix

            showUI(
                "Make tiled / MipMapped .exr", "Current File: " + filename + extension
            )

            IMG_CACHE = oiio.ImageCache.create(True)

            frameBufferOrig2 = ImageBuf(str(texture))

            outPutFile = str(Path(directory, filename + mipmapPrefix + mipmapExtension))

            writeFramebuffer = threadAndStatus(
                writeTexture, [frameBufferOrig2, outPutFile], "Saving", 0, False
            )

            IMG_CACHE.invalidate(str(texture))

        showUI("", Fore.GREEN + "All textures converted...")

    tqdm.write(prefix + "Press Enter to exit or close the Terminal")
    wait_key()


def main():
    parser = argparse.ArgumentParser(
        add_help=True,
        version=__version__,
        description=(__subTitle__ + "\n---\n" + __desc__),
        formatter_class=RawTextHelpFormatter,
    )

    parser.add_argument(
        "--adaptHDR",
        action="store_true",
        dest="adaptHDR",
        help="Processes hdrs in Adapt LookDev Scene folders\n\n",
    )
    parser.add_argument(
        "--textures",
        action="store_true",
        dest="textures",
        help="Processes all textures in current folder incl. all subfolders",
    )
    parser.add_argument(
        "--exclude",
        action="store",
        dest="folder",
        help="Excludes Folders from textures processing. Separated with ;",
    )

    results = parser.parse_args()

    if results.adaptHDR:
        processHDRs()
    elif results.textures:
        excludeFolders = results.folder.split(";")
        processTextures(excludeFolders)
    else:
        print(parser.parse_args(["-h"]))


if __name__ == "__main__":
    """This is executed when run from the command line."""
    try:
        sizex, sizey = get_terminal_size()
        width = sizex

        main()
    except (KeyboardInterrupt, KeyError) as e:
        print("\n")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
