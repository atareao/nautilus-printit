#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of nautilus-printi
#
# Copyright (C) 2016 Lorenzo Carbonell
# lorenzo.carbonell.cerezo@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#
import os
import threading
from urllib import unquote_plus
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Nautilus as FileManager
from printit.comun import _, EXTENSIONS_FROM
from printit.printdialog import PrintDialog


def get_files(files_in):
    files = []
    for file_in in files_in:
        print(file_in)
        file_in = unquote_plus(file_in.get_uri()[7:])
        if os.path.isfile(file_in):
            files.append(file_in)
    return files


class PrintItMenuProvider(GObject.GObject, FileManager.MenuProvider):
    """Implements the 'Replace in Filenames' extension to the File Manager
     right-click menu"""

    def __init__(self):
        """File Manager crashes if a plugin doesn't implement the __init__
         method"""
        pass

    def all_files_are_images(self, items):
        for item in items:
            fileName, fileExtension = os.path.splitext(
                unquote_plus(item.get_uri()[7:]))
            if fileExtension.lower() in EXTENSIONS_FROM:
                return True
        return False

    def printit(self, menu, selected):
        files = get_files(selected)
        printDialog = PrintDialog(_('Print'), files)
        if printDialog.run() == Gtk.ResponseType.ACCEPT:
            printDialog.pprint()
            '''
            images_per_page = printDialog.get_images_per_page()
            aprinter = printDialog.get_printer()
            orientation = printDialog.get_orientation()
            apapersize = printDialog.get_papersize()
            t = threading.Thread(target=pprint,
                                 args=(files, images_per_page, aprinter,
                                       orientation, apapersize))
            t.daemon = True
            t.start()
            '''

    def get_file_items(self, window, sel_items):
        """Adds the 'Replace in Filenames' menu item to the File Manager right
        -click menu, connects its 'activate' signal to the 'run' method
        passing the selected Directory/File"""
        if self.all_files_are_sounds(sel_items):
            top_menuitem = FileManager.MenuItem(
                name='PrintItMenuProvider::Gtk-printit-tools',
                label=_('Print images'),
                tip=_('Tool to print images'))
            top_menuitem.connect('activate', self.printit, sel_items)
            #
            return top_menuitem,
        return
if __name__ == '__main__':
    files = ['/home/lorenzo/Escritorio/sample1.jpg',
        '/home/lorenzo/Escritorio/sample2.jpg',
        '/home/lorenzo/Escritorio/sample1.jpg',
        '/home/lorenzo/Escritorio/sample2.jpg',
        '/home/lorenzo/Escritorio/sample1.jpg',
        '/home/lorenzo/Escritorio/sample2.jpg',
        '/home/lorenzo/Escritorio/sample1.jpg',
        '/home/lorenzo/Escritorio/sample2.jpg']
    printDialog = PrintDialog(_('Print'), files)
    if printDialog.run() == Gtk.ResponseType.ACCEPT:
        printDialog.hide()
        t = threading.Thread(target=printDialog.pprint)
        #t.daemon = True
        t.start()
        #printDialog.pprint()
