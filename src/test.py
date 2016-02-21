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
import cups

if __name__ == '__main__':
    conn = cups.Connection()
    devices = conn.getPrinters()
    for key in (devices.keys()):
        print('*****************************')
        print(devices[key])
        options = {'PageSize' : '29x90',
                   'BrMirror' : 'OFF',
                   'orientation-requested': '5'}
        conn.printFile('PDF',
                       '/home/lorenzo/Escritorio/sample1.jpg',
                       'sample',
                       options)
