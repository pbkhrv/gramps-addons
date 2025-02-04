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

# ------------------------------------------------------------------------
#
# GRAMPS modules
#
# ------------------------------------------------------------------------
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
from gramps.gen.lib import Person, Family, ChildRefType


def get_fsftid(person):
    for attr in person.get_attribute_list():
        if str(attr.get_type()) == "_FSFTID":
            return attr.get_value()
    return ""

# ------------------------------------------------------------------------
#
# Gramplet class
#
# ------------------------------------------------------------------------
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
            root_type = self.classify_root_type(person)
            if root_type:
                count += 1
                if count == 200:
                    # Why is this?
                    count = 0
                    yield True
                self.model.append(
                    (
                        person.handle,              # handle
                        simple_a.describe(person),  # name
                        root_type,                  # type
                        person.get_gramps_id(),     # I person id
                        get_fsftid(person),         # family search id
                        self.get_fids_list(person), # FI family ids
                    )
                )
        self.set_has_data(len(self.model) > 0)
        # print(time.perf_counter() - stime)

    def classify_root_type(self, person: Person):
        # - "Root": no parents, but has children
        # - "Sleeping": at least one spouse, no birth children
        # - "Detached": no parents, no family (and, by definition, no children)
        has_parents = len(person.get_parent_family_handle_list()) > 0
        is_married = len(person.get_family_handle_list()) > 0
        has_biological_child = self.has_biological_child_in_some_family(person)

        if not has_parents and has_biological_child:
            return "Root"
        elif not has_parents and not is_married:
            return "Detached"
        elif is_married and not has_biological_child:
            return "Sleeping"
        else:
            return None

    def has_biological_child_in_some_family(self, person: Person):
        def has_biological_child_in_family(family: Family):
            # Is person the father in this family?
            if family.get_father_handle() == person.get_handle():
                # find child with paternal "birth" link
                return any(
                    child_ref.get_father_relation() == ChildRefType.BIRTH
                    for child_ref in family.get_child_ref_list()
                )
            # Is person the mother in this family?
            elif family.get_mother_handle() == person.get_handle():
                # find child with maternal "birth" link
                return any(
                    child_ref.get_mother_relation() == ChildRefType.BIRTH
                    for child_ref in family.get_child_ref_list()
                )
            else:
                return False

        return any(
            has_biological_child_in_family(
                self.dbstate.db.get_family_from_handle(family_id)
            )
            for family_id in person.get_family_handle_list()
        )

    def get_fids_list(self, person: Person):
        out = ""
        for fh in person.get_family_handle_list():
            family: Family = self.dbstate.db.get_family_from_handle(fh)
            out += (", " if out else "") + family.get_gramps_id()
        return out

    def db_changed(self):
        self.connect(self.dbstate.db, "person-add", self.update)
        self.connect(self.dbstate.db, "person-delete", self.update)
        self.connect(self.dbstate.db, "family-add", self.update)
        self.connect(self.dbstate.db, "family-delete", self.update)
        self.connect(self.dbstate.db, "family-update", self.update)
        self.connect(self.dbstate.db, "person-rebuild", self.update)
        self.connect(self.dbstate.db, "family-rebuild", self.update)

    def build_gui(self):
        """
        Build the GUI interface.
        """
        tip = _("Click name to change active\n" "Double-click name to edit")
        self.set_tooltip(tip)
        top = Gtk.TreeView()
        selection = top.get_selection()
        selection.connect("changed", self.selection_changed)
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn(_("Person"), renderer, text=1)
        column.set_expand(True)
        column.set_resizable(True)
        column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        column.set_sort_column_id(1)
        top.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Root Type"), renderer, text=2)
        column.set_sort_column_id(2)
        top.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("PID"), renderer, text=3)
        column.set_sort_column_id(3)
        top.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("FSFTID"), renderer, text=4)
        column.set_sort_column_id(4)
        top.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("FIDs"), renderer, text=5)
        column.set_sort_column_id(5)
        top.append_column(column)

        self.model = Gtk.ListStore(
            str,  # handle
            str,  # name
            str,  # type
            str,  # person id
            str,  # family search id
            str,  # family ids
        )
        top.set_model(self.model)
        return top

    def selection_changed(self, selection):
        """
        Double-click for edit, single for make active.
        """
        model, iter_ = selection.get_selected()
        if iter_:
            handle = model.get_value(iter_, 0)
            self.uistate.set_active(handle, "Person")
