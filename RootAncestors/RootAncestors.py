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

import time

from gi.repository import Gtk, Gdk, Pango
#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gramps.gen.plug import Gramplet
from gramps.gen.const import GRAMPS_LOCALE as glocale
try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext
from gramps.gui.editors import EditPerson
from gramps.gen.simple import SimpleAccess
from gramps.gen.errors import WindowActiveError


#------------------------------------------------------------------------
#
# Gramplet class
#
#------------------------------------------------------------------------
class RootAncestorsGramplet(Gramplet):
    """
    Show a list of Persons without parents.
    """
    def init(self):
        self.gui.WIDGET = self.build_gui()
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add(self.gui.WIDGET)
        self.gui.WIDGET.show()

    def main(self):
        database = self.dbstate.db
        simple_a = SimpleAccess(database)
        # stime = time.perf_counter()
        count = 0
        self.model.clear()
        for person in database.iter_people():
            # Has no parents
            if not person.get_parent_family_handle_list():
                count += 1
                if count == 200:
                    # Why is this?
                    count = 0
                    yield True
                root_type = "Root" if simple_a.children(person) else "Detached"
                self.model.append((simple_a.describe(person), root_type, person.handle))
        self.set_has_data(len(self.model) > 0)
        # print(time.perf_counter() - stime)

    def db_changed(self):
        self.connect(self.dbstate.db, 'person-add', self.update)
        self.connect(self.dbstate.db, 'person-delete', self.update)
        self.connect(self.dbstate.db, 'family-add', self.update)
        self.connect(self.dbstate.db, 'family-delete', self.update)
        self.connect(self.dbstate.db, 'family-update', self.update)
        self.connect(self.dbstate.db, 'person-rebuild', self.update)
        self.connect(self.dbstate.db, 'family-rebuild', self.update)

    def build_gui(self):
        """
        Build the GUI interface.
        """
        tip = _("Click name to change active\n"
                "Double-click name to edit")
        self.set_tooltip(tip)
        top = Gtk.TreeView()
        selection = top.get_selection()
        selection.connect('changed', self.selection_changed)
        renderer = Gtk.CellRendererText()
        renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn(_('Person'), renderer, text=0)
        column.set_expand(True)
        column.set_resizable(True)
        column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        column.set_sort_column_id(0)
        top.append_column(column)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_('Root Type'), renderer, text=1)
        column.set_sort_column_id(1)
        top.append_column(column)
        self.model = Gtk.ListStore(str, str, str)
        top.set_model(self.model)
        return top

    def selection_changed(self, selection):
        """
        Double-click for edit, single for make active.
        """
        model, iter_ = selection.get_selected()
        if iter_:
            handle = model.get_value(iter_, 2)
            self.uistate.set_active(handle, 'Person')
