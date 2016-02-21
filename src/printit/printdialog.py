#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of nautilus-pdf-tools
#
# Copyright (C) 2012-2015 Lorenzo Carbonell
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
from gi.repository import Gtk
from gi.repository import GdkPixbuf
from miniview import MiniView
from PIL import Image
import cairo
import tempfile
import shlex
import subprocess
import comun
from comun import _, PORTRAIT, LANDSCAPE, MMTOPIXEL, MMTOPDF
import cups
import os
from miniview import A0, A1, A2, A3, A4, A5, create_image_surface_from_file

ADMISIBLE_PAPER_SIZES = ['A0', 'A1', 'A2', 'A3', 'A4', 'A5']


def create_temp_file():
    return tempfile.mkstemp(prefix='tmp_filemanager_printit_')[1]


def list_printers():
    con = cups.Connection()
    return con.getPrinters()


def select_index_in_combo(combo, index):
    combo.set_active(index)


def select_value_in_combo(combo, value):
    model = combo.get_model()
    for i, item in enumerate(model):
        if value == item[1]:
            combo.set_active(i)
            return
    combo.set_active(0)


def get_selected_value_in_combo(combo, index=0):
    model = combo.get_model()
    return model.get_value(combo.get_active_iter(), index)


def list_pagesize(aprinter):
    args = shlex.split(
        'lpoptions -d "%s" -l' %
        (aprinter))
    p = subprocess.Popen(
        args, bufsize=10000, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ans = p.communicate()[0]
    if p.returncode == 0:
        print(ans)
        if ans.find('PageSize/Page Size:') > -1:
            start = ans.find('PageSize/Page Size:')
            end = ans.find('\n', start)
            ans = ans[start + len('PageSize/Page Size:'):end].split()
            return ans
        else:
            raise ValueError('Not page sizes')
            return []
    raise ValueError(ans)
    return []


def list_resolution(aprinter):
    args = shlex.split(
        'lpoptions -d "%s" -l' %
        (aprinter))
    p = subprocess.Popen(
        args, bufsize=10000, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ans = p.communicate()[0]
    if p.returncode == 0:
        if ans.find('Resolution/Output Resolution:') > -1:
            start = ans.find('Resolution/Output Resolution:')
            end = ans.find('\n', start)
            ans = ans[start + len('Resolution/Output Resolution:'):end].split()
            return ans
        else:
            raise ValueError('Not resolutions')
            return []
    raise ValueError(ans)
    return []


class PrintDialog(Gtk.Dialog):
    def __init__(self, title, filenames=[]):
        Gtk.Dialog.__init__(self,
                            title,
                            None,
                            Gtk.DialogFlags.MODAL |
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_OK,
                             Gtk.ResponseType.ACCEPT,
                             Gtk.STOCK_CANCEL,
                             Gtk.ResponseType.CANCEL))
        self.set_default_size(400, 400)
        self.set_resizable(True)
        self.set_icon_from_file(comun.ICON)
        self.connect('destroy', self.close)
        #
        vbox = Gtk.VBox(spacing=5)
        vbox.set_border_width(5)
        self.get_content_area().add(vbox)
        #
        frame = Gtk.Frame()
        vbox.pack_start(frame, True, True, 0)
        #
        table = Gtk.Table(rows=2, columns=2, homogeneous=False)
        table.set_border_width(5)
        table.set_col_spacings(5)
        table.set_row_spacings(5)
        frame.add(table)
        #
        frame1 = Gtk.Frame()
        table.attach(frame1, 0, 2, 0, 1, xoptions=Gtk.AttachOptions.EXPAND,
                     yoptions=Gtk.AttachOptions.SHRINK)
        self.scrolledwindow1 = Gtk.ScrolledWindow()
        self.scrolledwindow1.set_size_request(400, 400)
        self.connect('key-release-event', self.on_key_release_event)
        frame1.add(self.scrolledwindow1)
        #
        self.viewport1 = MiniView()
        self.scrolledwindow1.add(self.viewport1)
        #
        self.scale = 100
        #
        #
        label = Gtk.Label(_('Images per page'))
        label.set_alignment(0, 0.5)
        table.attach(label, 0, 1, 1, 2,
                     xoptions=Gtk.AttachOptions.FILL,
                     yoptions=Gtk.AttachOptions.SHRINK)
        listStore = Gtk.ListStore(str, int)
        listStore.append(['1', 1])
        listStore.append(['2', 2])
        listStore.append(['4', 4])
        listStore.append(['6', 6])
        listStore.append(['8', 8])
        self.images_per_page = Gtk.ComboBox()
        self.images_per_page.set_model(listStore)
        cell1 = Gtk.CellRendererText()
        self.images_per_page.pack_start(cell1, True)
        self.images_per_page.add_attribute(cell1, 'text', 0)
        table.attach(self.images_per_page, 1, 2, 1, 2,
                     xoptions=Gtk.AttachOptions.FILL,
                     yoptions=Gtk.AttachOptions.SHRINK)
        select_value_in_combo(self.images_per_page, 1)
        self.images_per_page.connect('changed',
                                     self.on_images_per_page_changed)
        label = Gtk.Label(_('Orientation'))
        label.set_alignment(0, 0.5)
        table.attach(label, 0, 1, 2, 3,
                     xoptions=Gtk.AttachOptions.FILL,
                     yoptions=Gtk.AttachOptions.SHRINK)
        listStore = Gtk.ListStore(str, int)
        listStore.append([_('Portrait'), PORTRAIT])
        listStore.append([_('Landscape'), LANDSCAPE])
        self.orientations = Gtk.ComboBox()
        self.orientations.set_model(listStore)
        cell1 = Gtk.CellRendererText()
        self.orientations.pack_start(cell1, True)
        self.orientations.add_attribute(cell1, 'text', 0)
        table.attach(self.orientations, 1, 2, 2, 3,
                     xoptions=Gtk.AttachOptions.FILL,
                     yoptions=Gtk.AttachOptions.SHRINK)
        self.orientations.connect('changed', self.on_orientation_changed)
        select_value_in_combo(self.orientations, PORTRAIT)
        label = Gtk.Label(_('Printer'))
        label.set_alignment(0, 0.5)
        table.attach(label, 0, 1, 3, 4,
                     xoptions=Gtk.AttachOptions.FILL,
                     yoptions=Gtk.AttachOptions.SHRINK)
        listStore = Gtk.ListStore(str)
        for aprinter in list_printers():
            listStore.append([aprinter])
        self.printers = Gtk.ComboBox()
        self.printers.set_model(listStore)
        cell1 = Gtk.CellRendererText()
        self.printers.pack_start(cell1, True)
        self.printers.add_attribute(cell1, 'text', 0)
        table.attach(self.printers, 1, 2, 3, 4,
                     xoptions=Gtk.AttachOptions.FILL,
                     yoptions=Gtk.AttachOptions.SHRINK)
        self.printers.connect('changed', self.on_printer_changed)
        label = Gtk.Label(_('Paper size'))
        label.set_alignment(0, 0.5)
        table.attach(label, 0, 1, 4, 5,
                     xoptions=Gtk.AttachOptions.FILL,
                     yoptions=Gtk.AttachOptions.SHRINK)
        listStore = Gtk.ListStore(str)
        self.papersizes = Gtk.ComboBox()
        self.papersizes.set_model(listStore)
        cell1 = Gtk.CellRendererText()
        self.papersizes.pack_start(cell1, True)
        self.papersizes.add_attribute(cell1, 'text', 0)
        table.attach(self.papersizes, 1, 2, 4, 5,
                     xoptions=Gtk.AttachOptions.FILL,
                     yoptions=Gtk.AttachOptions.SHRINK)
        self.papersizes.connect('changed', self.on_papersize_changed)
        label = Gtk.Label(_('Resolution'))
        label.set_alignment(0, 0.5)
        table.attach(label, 0, 1, 5, 6,
                     xoptions=Gtk.AttachOptions.FILL,
                     yoptions=Gtk.AttachOptions.SHRINK)
        listStore = Gtk.ListStore(str)
        self.resolutions = Gtk.ComboBox()
        self.resolutions.set_model(listStore)
        cell1 = Gtk.CellRendererText()
        self.resolutions.pack_start(cell1, True)
        self.resolutions.add_attribute(cell1, 'text', 0)
        table.attach(self.resolutions, 1, 2, 5, 6,
                     xoptions=Gtk.AttachOptions.FILL,
                     yoptions=Gtk.AttachOptions.SHRINK)
        #
        self.filenames = filenames
        select_index_in_combo(self.printers, 0)
        #
        if len(self.filenames) == 0:
            self.images_per_page.set_sensitive(False)
        elif len(self.filenames) == 1:
            select_value_in_combo(self.images_per_page, 1)
            self.images_per_page.set_sensitive(False)
        #
        self.draw_images()
        self.show_all()

    def draw_images(self):
        if self.filenames > 0:
            self.viewport1.set_images(self.filenames)

    def on_images_per_page_changed(self, widget):
        images_per_page = get_selected_value_in_combo(self.images_per_page, 1)
        print('*************************************************')
        print(images_per_page)
        print('*************************************************')

        self.viewport1.set_images_per_page(images_per_page)

    def on_orientation_changed(self, widget):
        orientation = get_selected_value_in_combo(self.orientations, 1)
        print('*************************************************')
        print(orientation)
        print('*************************************************')
        self.viewport1.set_orientation(orientation)

    def on_papersize_changed(self, widget):
        apapersize = get_selected_value_in_combo(self.papersizes)
        if apapersize == 'A0':
            self.viewport1.set_page(A0)
        elif apapersize == 'A1':
            self.viewport1.set_page(A1)
        elif apapersize == 'A2':
            self.viewport1.set_page(A2)
        elif apapersize == 'A3':
            self.viewport1.set_page(A3)
        elif apapersize == 'A4':
            self.viewport1.set_page(A4)
        elif apapersize == 'A5':
            self.viewport1.set_page(A5)

    def on_printer_changed(self, widget):
        aprinter = get_selected_value_in_combo(self.printers)
        model = self.papersizes.get_model()
        model.clear()
        for apapersize in list_pagesize(aprinter):
            if apapersize.startswith('*'):
                apapersize = apapersize[1:]
            if apapersize in ADMISIBLE_PAPER_SIZES:
                model.append([apapersize])
        select_index_in_combo(self.papersizes, 0)
        model = self.resolutions.get_model()
        model.clear()
        for aresolution in list_resolution(aprinter):
            if aresolution.startswith('*'):
                aresolution = aresolution[1:]
            model.append([aresolution])
        select_index_in_combo(self.resolutions, 0)

    def get_images_per_page(self):
        return get_selected_value_in_combo(self.images_per_page, 1)

    def get_printer(self):
        return get_selected_value_in_combo(self.printers)

    def get_orientation(self):
        return get_selected_value_in_combo(self.orientations, 1)

    def get_papersize(self):
        return get_selected_value_in_combo(self.papersizes)

    def pprint(self):
        images_per_page = get_selected_value_in_combo(self.images_per_page, 1)
        aprinter = get_selected_value_in_combo(self.printers)
        orientation = get_selected_value_in_combo(self.orientations, 1)
        apapersize = get_selected_value_in_combo(self.papersizes)
        if apapersize == 'A0':
            width, height = A0.get_size()
        elif apapersize == 'A1':
            width, height = A1.get_size()
        elif apapersize == 'A2':
            width, height = A2.get_size()
        elif apapersize == 'A3':
            width, height = A3.get_size()
        elif apapersize == 'A4':
            width, height = A4.get_size()
        elif apapersize == 'A5':
            width, height = A5.get_size()
        if orientation == PORTRAIT:
            twidth = height
            height = width
            width = twidth
        temp_pdf = create_temp_file()
        pdfsurface = cairo.PDFSurface(temp_pdf,
                                      width / 25.4 * 72.0,
                                      height / 25.4 * 72.0)
        context = cairo.Context(pdfsurface)
        if images_per_page == 1 and len(self.filenames) > 0:
            for filename in self. filenames:
                image1 = create_image_surface_from_file(filename)
                w1 = image1.get_width() / MMTOPIXEL
                h1 = image1.get_height() / MMTOPIXEL
                zw = w1 / width
                zh = h1 / height
                if zw > zh:
                    z = zw
                else:
                    z = zh
                print(w1, h1)
                context.save()
                x = abs(w1 / z - width) / 2.0
                y = abs(h1 / z - height) / 2.0
                print(x, y)
                context.translate(x * 2.8343, y * 2.8343)
                context.scale(2.8343 / MMTOPIXEL / z, 2.8343 / MMTOPIXEL / z)
                context.set_source_surface(image1)
                context.paint()
                context.restore()
                context.show_page()
        elif images_per_page == 2 and len(self.filenames) >= 2:
            for contador in range(0, len(self. filenames), 2):
                for i in range(0, 2):
                    if(contador + i < len(self.filenames)):
                        image = create_image_surface_from_file(
                                self.filenames[contador + i])
                        w = image.get_width() / MMTOPIXEL
                        h = image.get_height() / MMTOPIXEL
                        zw = w / (width / 2.0)
                        zh = h / height
                        if zw > zh:
                            z = zw
                        else:
                            z = zh
                        context.save()
                        x = float(i) * width / 2.0 +\
                            abs(w / z - width / 2.0) / 2.0
                        y = abs(h / z - height) / 2.0
                        context.translate(x * 2.8343, y * 2.8343)
                        context.scale(2.8343 / MMTOPIXEL / z,
                                      2.8343 / MMTOPIXEL / z)
                        context.set_source_surface(image)
                        context.paint()
                        context.restore()
                context.show_page()
        elif images_per_page == 4 and len(self.filenames) >= 4:
            for contador in range(0, len(self. filenames), 4):
                for i in range(0, 4):
                    if(contador + i < len(self.filenames)):
                        image = create_image_surface_from_file(
                            self.filenames[contador + i])
                        w = image.get_width() / MMTOPIXEL
                        h = image.get_height() / MMTOPIXEL
                        zw = w / (width / 2.0)
                        zh = h / (height / 2.0)
                        if zw > zh:
                            z = zw
                        else:
                            z = zh
                        context.save()
                        x = float(i % 2) * width / 2.0 +\
                            abs(w / z - width / 2.0) / 2.0
                        y = float(i / 2) * height / 2.0 +\
                            abs(h / z - height / 2.0) / 2.0
                        print(x, y)
                        context.translate(x * 2.8343, y * 2.8343)
                        context.scale(2.8343 / MMTOPIXEL / z,
                                      2.8343 / MMTOPIXEL / z)
                        context.set_source_surface(image)
                        context.paint()
                        context.restore()
                context.show_page()
        elif images_per_page == 6 and len(self.filenames) >= 6:
            for contador in range(0, len(self. filenames), 6):
                for i in range(0, 6):
                    if(contador + i < len(self.filenames)):
                        image = create_image_surface_from_file(
                            self.filenames[contador + i])
                        w = image.get_width() / MMTOPIXEL
                        h = image.get_height() / MMTOPIXEL
                        zw = w / (width / 3.0)
                        zh = h / (height / 2.0)
                        if zw > zh:
                            z = zw
                        else:
                            z = zh
                        context.save()
                        x = float(i % 3) * width / 3.0 +\
                            abs(w / z - width / 3.0) / 2.0
                        y = float(i / 3) * height / 2.0 +\
                            abs(h / z - height / 2.0) / 2.0
                        context.translate(x * 2.8343, y * 2.8343)
                        context.scale(2.8343 / MMTOPIXEL / z,
                                      2.8343 / MMTOPIXEL / z)
                        context.set_source_surface(image)
                        context.paint()
                        context.restore()
                context.show_page()
        elif images_per_page == 8 and len(self.filenames) >= 8:
            for contador in range(0, len(self. filenames), 8):
                for i in range(0, 8):
                    if(contador + i < len(self.filenames)):
                        image = create_image_surface_from_file(
                            self.filenames[contador + i])
                        w = image.get_width() / MMTOPIXEL
                        h = image.get_height() / MMTOPIXEL
                        zw = w / (width / 4.0)
                        zh = h / (height / 2.0)
                        if zw > zh:
                            z = zw
                        else:
                            z = zh
                        context.save()
                        x = float(i % 4) * width / 4.0 +\
                            abs(w / z - width / 4.0) / 2.0
                        y = float(i / 4) * height / 2.0 +\
                            abs(h / z - height / 2.0) / 2.0
                        context.translate(x * 2.8343, y * 2.8343)
                        context.scale(2.8343 / MMTOPIXEL / z,
                                      2.8343 / MMTOPIXEL / z)
                        context.set_source_surface(image)
                        context.paint()
                        context.restore()
                context.show_page()
        pdfsurface.flush()
        pdfsurface.finish()
        if orientation == LANDSCAPE:
            printcommand = 'lp -d %s\
                            -o media=%s\
                            -o orientation-requested=4 "%s"' % (aprinter,
                                                                apapersize,
                                                                temp_pdf)
        else:
            printcommand = 'lp -d %s -o media=%s "%s"' % (aprinter,
                                                          apapersize,
                                                          temp_pdf)
        print(printcommand)
        args = shlex.split(printcommand)
        p = subprocess.Popen(args, bufsize=10000, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        ans = p.communicate()[0]
        if p.returncode == 0:
            print(ans)
        os.remove(temp_pdf)

    def on_key_release_event(self, widget, event):
        print((event.keyval))
        if event.keyval == 65451 or event.keyval == 43:
            self.scale = self.scale * 1.1
        elif event.keyval == 65453 or event.keyval == 45:
            self.scale = self.scale * .9
        elif event.keyval == 65456 or event.keyval == 48:
            pass
            '''
            factor_w = float(
                self.scrolledwindow1.get_allocation().width) /\
                float(self.pixbuf1.get_width())
            factor_h = float(
                self.scrolledwindow1.get_allocation().height) /\
                float(self.pixbuf1.get_height())
            if factor_w < factor_h:
                factor = factor_w
            else:
                factor = factor_h
            self.scale = int(factor * 100)
            w = int(self.pixbuf1.get_width() * factor)
            h = int(self.pixbuf1.get_height() * factor)
            #
            self.image1.set_from_pixbuf(
                self.pixbuf1.scale_simple(w, h,
                                          GdkPixbuf.InterpType.BILINEAR))
            self.image2.set_from_pixbuf(
                self.pixbuf2.scale_simple(w, h,
                                          GdkPixbuf.InterpType.BILINEAR))
        elif event.keyval == 65457 or event.keyval == 49:
            self.scale = 100
        if self.image1:
            w = int(self.pixbuf1.get_width() * self.scale / 100)
            h = int(self.pixbuf1.get_height() * self.scale / 100)
            #
            self.image1.set_from_pixbuf(
                self.pixbuf1.scale_simple(w, h,
                                          GdkPixbuf.InterpType.BILINEAR))
            self.image2.set_from_pixbuf(
                self.pixbuf2.scale_simple(w, h,
                                          GdkPixbuf.InterpType.BILINEAR))
            '''

    def close(self, widget):
        self.destroy()

if __name__ == '__main__':
    dialog = PrintDialog('Test', ['/home/lorenzo/Escritorio/sample1.jpg',
        '/home/lorenzo/Escritorio/sample2.jpg',
        '/home/lorenzo/Escritorio/sample1.jpg',
        '/home/lorenzo/Escritorio/sample2.jpg',
        '/home/lorenzo/Escritorio/sample1.jpg',
        '/home/lorenzo/Escritorio/sample2.jpg',
        '/home/lorenzo/Escritorio/sample1.jpg',
        '/home/lorenzo/Escritorio/sample2.jpg'])
    ans = dialog.run()
    print(ans)
    if ans == Gtk.ResponseType.ACCEPT:
        print(1)
        dialog.pprint()
    exit(0)

