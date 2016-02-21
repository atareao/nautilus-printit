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
from gi.repository import Gdk
from gi.repository import GdkPixbuf
import cairo
import math

from comun import RESOLUTION, MMTOPIXEL, TOP, MIDLE, BOTTOM,\
    LEFT, CENTER, RIGHT, PORTRAIT, LANDSCAPE


def create_image_surface_from_file(filename):
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
    return create_image_surface_from_pixbuf(pixbuf)


def create_image_surface_from_pixbuf(pixbuf):
    surface = cairo.ImageSurface(
        cairo.FORMAT_ARGB32, pixbuf.get_width(), pixbuf.get_height())
    context = cairo.Context(surface)
    Gdk.cairo_set_source_pixbuf(context, pixbuf, 0, 0)
    context.paint()
    return surface


class Page():
    def __init__(self, width=-1, height=-1, orientation=PORTRAIT):
        self.width = width
        self.height = height
        self.orientation = orientation

    def get_width(self):
        return self.width

    def set_width(self, width):
        self.width = width

    def get_height(self):
        return self.height

    def set_height(self, height):
        self.height = height

    def get_size(self):
        return self.width, self.height

A0 = Page(1189.0, 841.0, LANDSCAPE)
A1 = Page(841.0, 594.0, LANDSCAPE)
A2 = Page(594.0, 420.0, LANDSCAPE)
A3 = Page(420.0, 297.0, LANDSCAPE)
A4 = Page(297.0, 210.0, LANDSCAPE)
A5 = Page(210.0, 148.0, LANDSCAPE)
A6 = Page(148.0, 105.0, LANDSCAPE)
A7 = Page(105.0, 74.0, LANDSCAPE)
A8 = Page(74.0, 52.0, LANDSCAPE)
LETTER = Page(279.0, 216.0, LANDSCAPE)
FOLIO = Page(330.0, 216.0, LANDSCAPE)
LEGAL = Page(356.0, 216.0, LANDSCAPE)
TABLOID = Page(432.0, 279.0, LANDSCAPE)


class MiniView(Gtk.DrawingArea):
    def __init__(self, width=400.0, height=420.00, margin=10.0,
                 border=2.0, force=False):
        Gtk.DrawingArea.__init__(self)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.height = height
        self.width = width
        self.image_surface = None
        self.margin = margin
        self.border = border
        self.page = None
        self.zoom = 1
        self.orientation = PORTRAIT
        self.page_width = -1
        self.page_height = -1
        self.margin_width = -1
        self.margin_height = -1
        self.images = []
        self.images_per_page = 1
        self.connect('draw', self.on_expose, None)
        self.set_size_request(self.width, self.height)

    def on_expose(self, widget, cr, data):
        if self.page:
            if self.orientation == LANDSCAPE:
                zw = (self.width - 2.0 * self.margin) / self.or_width
                zh = (self.height - 2.0 * self.margin) / self.or_height
                if zw < zh:
                    self.zoom = zw
                else:
                    self.zoom = zh
                self.page_width = self.or_width * self.zoom
                self.page_height = self.or_height * self.zoom
                self.margin_width = (self.width - self.page_width) / 2.0
                self.margin_height = (self.height - self.page_height) / 2.0
            else:
                zw = (self.width - 2.0 * self.margin) / self.or_height
                zh = (self.height - 2.0 * self.margin) / self.or_width
                if zw < zh:
                    self.zoom = zw
                else:
                    self.zoom = zh
                self.page_width = self.or_height * self.zoom
                self.page_height = self.or_width * self.zoom
                self.margin_width = (self.width - self.page_width) / 2.0
                self.margin_height = (self.height - self.page_height) / 2.0
            self.image_surface = cairo.ImageSurface(
                cairo.FORMAT_RGB24,
                int(self.page_width),
                int(self.page_height))
            context = cairo.Context(self.image_surface)
            context.save()
            context.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            context.paint()
            mtr = cairo.Matrix()
            if self.orientation == LANDSCAPE:
                mtr.rotate(math.pi / 2.0)
            mtr.scale(self.zoom * RESOLUTION, self.zoom * RESOLUTION)
            context.transform(mtr)
            if self.orientation == PORTRAIT:
                context.translate(
                    0.0, -self.page_width / self.zoom / RESOLUTION)
            elif self.orientation == LANDSCAPE:
                context.translate(-self.page_width / self.zoom /
                                  RESOLUTION, -self.page_height / self.zoom /
                                  RESOLUTION)
            context.restore()
            if len(self.images) > 0:
                if self.orientation == LANDSCAPE:
                    main_width = self.or_width
                    main_height = self.or_height
                else:
                    main_width = self.or_height
                    main_height = self.or_width
                if self.images_per_page == 1:
                    image = create_image_surface_from_file(self.images[0])
                    width = image.get_width() / MMTOPIXEL
                    height = image.get_height() / MMTOPIXEL
                    zw = width / main_width
                    zh = height / main_height
                    if zw > zh:
                        z = zw
                    else:
                        z = zh
                    x = abs(width / z - main_width) / 2.0
                    y = abs(height / z - main_height) / 2.0
                    context.save()
                    context.translate(x * self.zoom, y * self.zoom)
                    context.scale(self.zoom / MMTOPIXEL / z,
                                  self.zoom / MMTOPIXEL / z)
                    context.set_source_surface(image)
                    context.paint()
                    context.restore()
                elif self.images_per_page == 2 and len(self.images) >= 2:
                    for i in range(0, 2):
                        image = create_image_surface_from_file(self.images[i])
                        width = image.get_width() / MMTOPIXEL
                        height = image.get_height() / MMTOPIXEL
                        zw = width / (main_width / 2.0)
                        zh = height / main_height
                        if zw > zh:
                            z = zw
                        else:
                            z = zh
                        x = float(i) * main_width / 2.0 +\
                            abs(width / z - main_width / 2.0) / 2.0
                        y = abs(height / z - main_height) / 2.0
                        context.save()
                        context.translate(x * self.zoom, y * self.zoom)
                        context.scale(self.zoom / MMTOPIXEL / z,
                                      self.zoom / MMTOPIXEL / z)
                        context.set_source_surface(image)
                        context.paint()
                        context.restore()
                elif self.images_per_page == 4 and len(self.images) >= 4:
                    for i in range(0, 4):
                        image = create_image_surface_from_file(self.images[i])
                        width = image.get_width() / MMTOPIXEL
                        height = image.get_height() / MMTOPIXEL
                        zw = width / (main_width / 2.0)
                        zh = height / (main_height / 2.0)
                        if zw > zh:
                            z = zw
                        else:
                            z = zh
                        x = float(i % 2) * main_width / 2.0 +\
                            abs(width / z - main_width / 2.0) / 2.0
                        y = float(i / 2) * main_height / 2.0 +\
                            abs(height / z - main_height / 2.0) / 2.0
                        context.save()
                        context.translate(x * self.zoom, y * self.zoom)
                        context.scale(self.zoom / MMTOPIXEL / z,
                                      self.zoom / MMTOPIXEL / z)
                        context.set_source_surface(image)
                        context.paint()
                        context.restore()
                elif self.images_per_page == 6 and len(self.images) >= 6:
                    for i in range(0, 6):
                        image = create_image_surface_from_file(self.images[i])
                        width = image.get_width() / MMTOPIXEL
                        height = image.get_height() / MMTOPIXEL
                        zw = width / (main_width / 3.0)
                        zh = height / (main_height / 2.0)
                        if zw > zh:
                            z = zw
                        else:
                            z = zh
                        x = float(i % 3) * main_width / 3.0 +\
                            abs(width / z - main_width / 3.0) / 2.0
                        y = float(i / 3) * main_height / 2.0 +\
                            abs(height / z - main_height / 2.0) / 2.0
                        context.save()
                        context.translate(x * self.zoom, y * self.zoom)
                        context.scale(self.zoom / MMTOPIXEL / z,
                                      self.zoom / MMTOPIXEL / z)
                        context.set_source_surface(image)
                        context.paint()
                        context.restore()
                elif self.images_per_page == 8 and len(self.images) >= 8:
                    for i in range(0, 8):
                        image = create_image_surface_from_file(self.images[i])
                        width = image.get_width() / MMTOPIXEL
                        height = image.get_height() / MMTOPIXEL
                        zw = width / (main_width / 4.0)
                        zh = height / (main_height / 2.0)
                        if zw > zh:
                            z = zw
                        else:
                            z = zh
                        x = float(i % 4) * main_width / 4.0 +\
                            abs(width / z - main_width / 4.0) / 2.0
                        y = float(i / 4) * main_height / 2.0 +\
                            abs(height / z - main_height / 2.0) / 2.0
                        context.save()
                        context.translate(x * self.zoom, y * self.zoom)
                        context.scale(self.zoom / MMTOPIXEL / z,
                                      self.zoom / MMTOPIXEL / z)
                        context.set_source_surface(image)
                        context.paint()
                        context.restore()



        cr.save()
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.5)
        cr.rectangle(self.margin_width - self.border,
                     self.margin_height - self.border,
                     self.page_width + 2.0 * self.border,
                     self.page_height + 2.0 * self.border)
        cr.stroke()
        cr.restore()
        #
        if self.page:
            cr.set_source_surface(
                self.image_surface, self.margin_width, self.margin_height)
            cr.paint()

    def set_page(self, page):
        self.page = page
        self.rotation_angle = 0.0
        self.drawings = []
        self.or_width, self.or_height = self.page.get_size()
        self.or_width = int(self.or_width * RESOLUTION)
        self.or_height = int(self.or_height * RESOLUTION)
        self.queue_draw()

    def set_orientation(self, orientation):
        self.orientation = orientation
        self.queue_draw()

    def add_image(self, image):
        self.images.append(image)
        self.queue_draw()

    def set_images(self, images):
        self.images = images
        self.queue_draw()

    def set_images_per_page(self, images_per_page):
        self.images_per_page = images_per_page
        self.queue_draw()

    def refresh(self):
        self.queue_draw()
