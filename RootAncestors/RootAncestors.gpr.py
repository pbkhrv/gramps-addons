# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009  Douglas S. Blank <doug.blank@gmail.com>
# Copyright (C) 2016  Serge Noiraud <serge.noiraud@free.fr>
# Copyright (C) 2017  Paul Culley <paulr2787@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
register(GRAMPLET,
         id="Root Ancestors Gramplet",
         name=_("Root Ancestors"),
         description = _("Gramplet for finding connection points in family trees"),
         status= STABLE,
         fname="RootAncestors.py",
         authors=["Peter"],
         authors_email=["pbkhrv@pm.me"],
         height=300,
         expand=True,
         gramplet = "RootAncestorsGramplet",
         gramplet_title=_("Root Ancestors"),
         detached_width = 600,
         detached_height = 400,
         version = '0.3.0',
         gramps_target_version = "5.2",
         help_url="Descendant_Count_Gramplet",
         )
