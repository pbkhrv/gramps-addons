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
            # Has no parents
            if not person.get_parent_family_handle_list():
                count += 1
                if count == 200:
                    # Why is this?
                    count = 0
                    yield True
                root_type = self.classify_root_type(person)
                self.model.append(
                    (
                        person.handle,
                        simple_a.describe(person),
                        len(person.get_family_handle_list()),
                        get_fsftid(person),
                        root_type,
                    )
                )
        self.set_has_data(len(self.model) > 0)
        # print(time.perf_counter() - stime)

    def classify_root_type(self, person):
        # - "Root": no parents, but has children
        # - "Leaf": no children in any family but a spouse has children in one of their families
        # - "Sleeper": no children, at least one spouse, but no spouses have children
        # - "Detached": no parents, no family (and, by definition, no children)
        a_spouse_has_children_in_some_family = any(
            (spouse := self.spouse_in_family(person, family_id))
            and self.has_children_in_any_family(spouse)
            for family_id in person.get_family_handle_list()
        )

        no_spouse_has_parents = all(
            (spouse := self.spouse_in_family(person, family_id))
            and not spouse.get_parent_family_handle_list()
            for family_id in person.get_family_handle_list()
        )

        if self.has_children_in_any_family(person):
            return "Root"
        elif a_spouse_has_children_in_some_family:
            return "Leaf"
        elif (
            len(person.get_family_handle_list()) == 1
            and no_spouse_has_parents
            and not a_spouse_has_children_in_some_family
        ):
            return "Sleeper"
        else:
            return "Detached"

    def has_children_in_any_family(self, person):
        has_children = lambda family: len(family.get_child_ref_list()) > 0
        return any(
            has_children(self.dbstate.db.get_family_from_handle(family_id))
            for family_id in person.get_family_handle_list()
        )

    def spouse_in_family(self, person, family_id):
        family = self.dbstate.db.get_family_from_handle(family_id)
        if family.get_father_handle() == person.get_handle():
            return self.dbstate.db.get_person_from_handle(family.get_mother_handle())
        elif family.get_mother_handle() == person.get_handle():
            return self.dbstate.db.get_person_from_handle(family.get_father_handle())
        else:
            return None

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
        column = Gtk.TreeViewColumn(_("Families"), renderer, text=2)
        column.set_sort_column_id(2)
        top.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("FSFTID"), renderer, text=3)
        column.set_sort_column_id(3)
        top.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Root Type"), renderer, text=4)
        column.set_sort_column_id(4)
        top.append_column(column)

        self.model = Gtk.ListStore(
            str,  # handle
            str,  # name
            int,  # family count
            str,  # family search id
            str,  # root type
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
