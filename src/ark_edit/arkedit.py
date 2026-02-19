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
        self.main_layout = Gtk.Grid()
        self.window.set_child(self.main_layout)

        # Login
        self.username_label = Gtk.Label(label="Username")
        self.username_input = Gtk.Entry()
        self.password_label = Gtk.Label(label="Password")
        self.password_input = Gtk.PasswordEntry()
        self.login_button = Gtk.Button(label="Log In")
        self.login_container = Gtk.Grid()

        self.login_button.connect("clicked", self.login)

        self.login_container.attach(self.username_label, 0, 0, 1, 1)
        self.login_container.attach(self.username_input, 1, 0, 1, 1)
        self.login_container.attach(self.password_label, 2, 0, 1, 1)
        self.login_container.attach(self.password_input, 3, 0, 1, 1)
        self.login_container.attach(self.login_button, 4, 0, 1, 1)

        # Search
        self.search_container = Gtk.Grid()
        self.search_label = Gtk.Label(label="Search")
        self.search_input = Gtk.SearchEntry()
        self.search_button = Gtk.Button(label="Search")

        self.search_button.connect("clicked", self.search)

        self.search_container.attach(self.search_label, 0, 0, 1, 1)
        self.search_container.attach(self.search_input, 1, 0, 1, 1)
        self.search_container.attach(self.search_button, 2, 0, 1, 1)

        # Results
        self.results_container = Gtk.Grid()
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

        self.add_edit_field_button.connect("clicked", self.add_new_edit_field)

        self.add_edit_field_container.attach(
            self.add_edit_field_label, 0, 0, 1, 1
        )
        self.add_edit_field_container.attach(
            self.add_edit_field_key_input, 1, 0, 1, 1
        )
        self.add_edit_field_container.attach(
            self.add_edit_field_value_input, 2, 0, 1, 1
        )
        self.add_edit_field_container.attach(
            self.add_edit_field_button, 2, 2, 1, 1
        )

        # Layout
        self.main_layout.attach(self.login_container, 0, 0, 5, 1)
        self.main_layout.attach(self.search_container, 1, 1, 4, 2)
        self.main_layout.attach(self.results_scroll, 0, 1, 1, 10)
        self.main_layout.attach(
            self.edit_container, 1, 3, 4, len(self.ark.keys())
        )
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

    def populate_edit_container(self, md):
        # Clear old fields
        self.clear_rows(self.edit_container)

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

    def add_new_edit_field(self, _):
        row = len(self.edit_fields.keys()) + 1
        key = self.add_edit_field_key_input.props.text
        value = self.add_edit_field_value_input.props.text

        self.edit_container.insert_row(row)
        self.add_edit_field(row, key, value)
        # Save method currently depends on all edit fields
        # having matching ARK keys, including add fields
        self.ark[key] = value

    def login(self, _):
        self.username = self.username_input.props.text
        self.password = self.password_input.props.text

    def save(self, _):
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
            ezid.upload_anvl(
                self.username, self.password, shoulder, anvl, action
            )
        except AttributeError:
            pass

    def edit_ark(self, button):
        ark = button.props.name
        ## Need to fix, all search results return same ark, problem probably with self.search
        ark = ezid.anvl_to_dict(
            ezid.view_anvl(self.username, self.password, ark)
        )
        ark["ark"] = ark["success"]
        del ark["success"]
        self.ark = ark
        self.populate_edit_container(ark)

    def search(self, _):
        ## Need to fix, all search results return same ark in self.edit, problem probably with self.search
        self.results = list(
            ezid.query(
                keywords=self.search_input.props.text,
                username=self.username,
                password=self.password,
            )
        )
        # Clear any existing results
        self.clear_rows(self.results_container)
        for i, r in enumerate(self.results):
            button = Gtk.Button(
                label=f"{r['ark']}\n{r['title'][:21]}", name=r["ark"]
            )
            button.connect("clicked", self.edit_ark)
            self.results_container.attach(
                button,
                0,
                i,
                1,
                1,
            )

    def clear_rows(self, parent_grid):
        while parent_grid.get_child_at(0, 0):
            parent_grid.remove_row(0)


def main():
    app = ARKEdit()
    app.run()


if __name__ == "__main__":
    main()
