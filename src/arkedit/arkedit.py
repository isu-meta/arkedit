from arkimedes import ezid
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk


class ARKEdit(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="edu.iastate.lib.ARKEdit")
        GLib.set_application_name("ARKEdit")

        self.ark = {
            "ark": "",
            "dc.title": "",
            "dc.creator": "",
            "dc.date": "",
            "_target": "",
        }
        self.username = ""
        self.password = ""
        self.results = []
        self.edit_fields = {}

    def do_activate(self):
        self.window = Gtk.ApplicationWindow(application=self, title="ARKEdit")
        self.window.connect("destroy", self.window.close)
        self.main_layout = Gtk.Grid(row_spacing=10)
        self.window.set_child(self.main_layout)

        # Login
        self.username_label = Gtk.Label(
            label="Username", justify=Gtk.Justification.RIGHT
        )
        self.username_input = Gtk.Entry()
        self.password_label = Gtk.Label(label="Password", halign=Gtk.Align.END)
        self.password_input = Gtk.PasswordEntry(name="password", show_peek_icon=True)
        self.login_button = Gtk.Button(label="Log In")
        self.login_container = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=5
        )

        self.password_input.connect("activate", self.login)
        self.login_button.connect("clicked", self.login)

        self.login_container.append(self.username_label)
        self.login_container.append(self.username_input)
        self.login_container.append(self.password_label)
        self.login_container.append(self.password_input)
        self.login_container.append(self.login_button)

        # Search
        self.search_container = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=5
        )
        self.search_label = Gtk.Label(label="Search")
        self.search_input = Gtk.SearchEntry(name="search")
        self.search_button = Gtk.Button(label="Search")

        self.search_input.connect("activate", self.search)
        self.search_button.connect("clicked", self.search)

        self.search_container.append(self.search_label)
        self.search_container.append(self.search_input)
        self.search_container.append(self.search_button)

        # Results
        self.results_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.results_scroll = Gtk.ScrolledWindow()

        self.results_scroll.set_child(self.results_container)

        # Edit

        self.edit_container = Gtk.Grid()
        self.populate_edit_container(self.ark)

        # Add
        self.add_edit_field_label = Gtk.Label(label="Add field")
        self.add_edit_field_key_input = Gtk.Entry()
        self.add_edit_field_value_input = Gtk.Entry()
        self.add_edit_field_button = Gtk.Button(label="Add")
        self.add_edit_field_container = Gtk.Grid()

        self.add_edit_field_value_input.connect("activate", self.add_new_edit_field)
        self.add_edit_field_button.connect("clicked", self.add_new_edit_field)

        self.add_edit_field_container.attach(self.add_edit_field_label, 0, 0, 1, 1)
        self.add_edit_field_container.attach(self.add_edit_field_key_input, 1, 0, 1, 1)
        self.add_edit_field_container.attach(
            self.add_edit_field_value_input, 2, 0, 1, 1
        )
        self.add_edit_field_container.attach(self.add_edit_field_button, 2, 2, 1, 1)

        # Login required alert
        self.login_required = Gtk.AlertDialog(
            message="Login Required",
            detail="Please log in and try again.",
        )

        # Layout
        self.main_layout.attach(self.login_container, 1, 0, 6, 1)
        self.main_layout.attach(self.search_container, 0, 1, 4, 2)
        self.main_layout.attach(self.results_scroll, 0, 3, 3, 10)
        self.main_layout.attach(self.edit_container, 4, 4, 4, len(self.ark.keys()))
        self.main_layout.attach_next_to(
            self.add_edit_field_container,
            self.edit_container,
            Gtk.PositionType.BOTTOM,
            4,
            1,
        )

        # Show
        self.window.present()

    def add_edit_field(self, i, k, v):
        label = Gtk.Label(label=k)
        entry = Gtk.Entry(text=v)
        self.edit_fields[k] = entry
        self.edit_container.attach(label, 0, i, 1, 1)
        self.edit_container.attach(entry, 1, i, 1, 1)

    def add_new_edit_field(self, _):
        row = len(self.edit_fields.keys()) + 1
        key = self.add_edit_field_key_input.props.text
        value = self.add_edit_field_value_input.props.text

        # Clear inputs
        self.add_edit_field_key_input.props.text = ""
        self.add_edit_field_value_input.props.text = ""

        self.edit_container.insert_row(row)
        self.add_edit_field(row, key, value)
        # Save method currently depends on all edit fields
        # having matching ARK keys, including add fields
        self.ark[key] = value

    def populate_edit_container(self, md):
        # Clear old fields
        self.clear_grid_rows(self.edit_container)

        # Clear edit fields
        self.edit_fields = {}
        # Add new fields
        for i, (k, v) in enumerate(md.items()):
            self.add_edit_field(i, k, v)

        self.save_button = Gtk.Button(label="Save")
        self.save_button.connect("clicked", self.save)
        self.edit_container.attach(
            self.save_button, 1, len(self.edit_fields.keys()) + 1, 1, 1
        )

    def login(self, _):
        self.username = self.username_input.props.text
        self.password = self.password_input.props.text

    def save(self, _):
        if self.check_logged_in():
            for k in self.ark.keys():
                self.ark[k] = self.edit_fields[k].props.text
            if self.ark["ark"] != "":
                action = "update"
                shoulder = self.ark["ark"]
            else:
                action = "mint"
                shoulder = "ark:/87292/w9"

            anvl = ezid.build_anvl(
                {
                    k: v
                    for k, v in self.ark.items()
                    if k not in {"ark", "_ownergroup", "_created", "_updated"}
                }
            )

            try:
                ezid.upload_anvl(self.username, self.password, shoulder, anvl, action)
            except AttributeError:
                pass

    def edit_ark(self, button):
        ark = button.props.name
        ## Need to fix, all search results return same ark, problem probably with self.search
        ark = ezid.anvl_to_dict(ezid.view_anvl(self.username, self.password, ark))
        ark["ark"] = ark["success"]
        del ark["success"]
        self.ark = ark
        self.populate_edit_container(ark)

    def search(self, _):
        if self.check_logged_in():
            self.clear_box_children(self.results_container)
            searching = Gtk.Label(label="Searching...")
            self.results_container.append(searching)
            self.results = list(
                ezid.query(
                    keywords=self.search_input.props.text,
                    username=self.username,
                    password=self.password,
                )
            )
            # Clear any existing results
            self.clear_box_children(self.results_container)
            if len(self.results) > 0:
                for i, r in enumerate(self.results):
                    button = Gtk.Button(
                        label=f"{r['ark']}\n{r['title'][:21]}", name=r["ark"]
                    )
                    button.connect("clicked", self.edit_ark)
                    self.results_container.append(button)
            else:
                self.results.container.append(Label(label="No matches found."))

    def clear_grid_rows(self, parent_grid):
        parent_grid
        while parent_grid.get_child_at(0, 0):
            parent_grid.remove_column(0)

    def clear_box_children(self, box):
        while child := box.get_first_child():
            box.remove(child)

    def check_logged_in(self):
        if "" in {self.username, self.password}:
            self.login_required.show()
            return False
        else:
            return True


def main():
    app = ARKEdit()
    app.run()


if __name__ == "__main__":
    main()
