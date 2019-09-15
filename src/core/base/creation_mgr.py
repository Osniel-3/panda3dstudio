from .base import *
from .mgr import CoreManager as Mgr


class CreationPhaseManager:

    _id_generator = id_generator()

    def __init__(self, obj_type, has_color=False, add_to_hist=False):

        self._obj = None
        self._obj_type = obj_type
        self._has_color = has_color
        self._add_to_hist = add_to_hist
        self._custom_obj_name = ""

        self._origin_pos = Point3()
        self._creation_start_func = None
        self._creation_handlers = []
        self._current_creation_phase = 0

        if has_color:
            self.set_next_object_color()
        else:
            GD[f"next_{obj_type}_color"] = None

        Mgr.expose(f"custom_{obj_type}_name", lambda: self._custom_obj_name)
        Mgr.accept(f"set_custom_{obj_type}_name", self.__set_custom_object_name)

    def setup(self, creation_phases, status_text):

        creation_status = {}
        mode_text = f"Create {status_text['obj_type']}"
        info_text = "LMB-drag to start creation"
        creation_status["idle"] = {"mode": mode_text, "info": info_text}
        info_text = "[SNAP] LMB-drag to start creation"
        creation_status["snap_idle"] = {"mode": mode_text, "info": info_text}

        add_state = Mgr.add_state
        bind = Mgr.bind_state
        state_persistence = -12

        for i, phase_data in enumerate(creation_phases):

            main_starter, main_handler = phase_data

            if i == 0:
                self._creation_start_func = main_starter
                creation_starter = self.__get_creation_starter()
                Mgr.accept(f"start_{self._obj_type}_creation", creation_starter)
                on_enter_state = self.__enter_creation_start_phase
            else:
                on_enter_state = self.__get_creation_phase_starter(main_starter)

            on_exit_state = self.__exit_creation_phase

            state_id = f"{self._obj_type}_creation_phase_{i + 1}"
            add_state(state_id, state_persistence, on_enter_state, on_exit_state)

            self._creation_handlers.append(self.__get_creation_phase_handler(main_handler))

            binding_id = f"{self._obj_type} creation -> navigate"
            bind(state_id, binding_id, "space", lambda: Mgr.enter_state("navigation_mode"))
            binding_id = f"quit {self._obj_type} creation"
            bind(state_id, binding_id, "escape", self.__end_creation)
            binding_id = f"abort {self._obj_type} creation"
            bind(state_id, binding_id, "focus_loss", self.__end_creation)
            binding_id = f"cancel {self._obj_type} creation"
            bind(state_id, binding_id, "mouse3", self.__end_creation)

            info_text = f"move mouse to {status_text[f'phase{i + 1}']};"
            get_command = lambda state_id: lambda: Mgr.enter_state(state_id)

            if i == len(creation_phases) - 1:
                binding_id = f"finalize {self._obj_type} creation"
                bind(state_id, binding_id, "mouse1-up",
                     lambda: self.__end_creation(cancel=False))
                info_text += " release LMB to finalize;"
            else:
                binding_id = f"start {self._obj_type} creation phase {i + 2}"
                next_state_id = f"{self._obj_type}_creation_phase_{i + 2}"
                bind(state_id, binding_id, "mouse1-up", get_command(next_state_id))
                info_text += " release LMB to set;"

            info_text += " RMB to cancel; <Space> to navigate"
            creation_status[f"phase{i + 1}"] = {"mode": mode_text, "info": info_text}

        status_data = GD["status"]["create"]
        status_data[self._obj_type] = creation_status

        return True

    def __enter_creation_start_phase(self, prev_state_id, active):

        if active:
            Mgr.do("enable_view_gizmo", False)
            Mgr.do("set_view_gizmo_mouse_region_sort", 0)
            Mgr.update_remotely("interactive_creation", "resumed")

        snap_settings = GD["snap"]

        if snap_settings["on"]["creation"]:

            snap_type = "creation_phase_1"
            snap_on = snap_settings["on"][snap_type]
            snap_tgt_type = snap_settings["tgt_type"][snap_type]

            if snap_on and snap_tgt_type != "increment":
                snap_settings["type"] = snap_type
                Mgr.do("init_snap_target_checking", "create")

        self._creation_start_func()
        Mgr.add_task(self._creation_handlers[0], "draw_object", sort=3)
        Mgr.update_app("status", ["create", self._obj_type, "phase1"])

    def __exit_creation_phase(self, next_state_id, active):

        if active:
            Mgr.remove_task("draw_object")
            Mgr.do("enable_view_gizmo", True)
            Mgr.do("set_view_gizmo_mouse_region_sort", 210)

        self.__disable_snap()

    def __get_creation_starter(self):

        def start_creation(origin_pos):

            self._origin_pos = origin_pos
            self._current_creation_phase = 1

            Mgr.enter_state(f"{self._obj_type}_creation_phase_1")

        return start_creation

    def __get_creation_phase_starter(self, main_start_func):

        def start_creation_phase(prev_state_id, active):

            phase_id = self._current_creation_phase

            if active:
                Mgr.do("enable_view_gizmo", False)
                Mgr.do("set_view_gizmo_mouse_region_sort", 0)
                Mgr.update_remotely("interactive_creation", "resumed")
            else:
                phase_id += 1
                self._current_creation_phase = phase_id

            snap_settings = GD["snap"]

            if snap_settings["on"]["creation"]:

                snap_type = f"creation_phase_{phase_id - 1}"
                snap_on = snap_settings["on"][snap_type]
                snap_tgt_type = snap_settings["tgt_type"][snap_type]

                if snap_on:
                    if snap_tgt_type != "increment":
                        Mgr.do("end_snap_target_checking")
                        Mgr.set_cursor("create")
                    if snap_tgt_type == "grid_point" and not active:
                        Mgr.update_app("active_grid_plane", GD["active_grid_plane"])

                snap_type = f"creation_phase_{phase_id}"
                snap_on = snap_settings["on"][snap_type]
                snap_tgt_type = snap_settings["tgt_type"][snap_type]

                if snap_on and snap_tgt_type != "increment":
                    snap_settings["type"] = snap_type
                    Mgr.do("init_snap_target_checking", "create")

            Mgr.remove_task("draw_object")
            main_start_func()
            creation_handler = self._creation_handlers[phase_id - 1]
            Mgr.add_task(creation_handler, "draw_object", sort=3)
            Mgr.update_app("status", ["create", self._obj_type, f"phase{phase_id}"])

        return start_creation_phase

    def __get_creation_phase_handler(self, main_handler_func):

        def handle_creation_phase(task):

            main_handler_func()

            return task.cont

        return handle_creation_phase

    def __set_custom_object_name(self, custom_name):

        self._custom_obj_name = custom_name

    def init_object(self, obj):

        self._obj = obj

    def get_object(self):

        return self._obj

    def get_object_type(self):

        return self._obj_type

    def generate_object_id(self):

        obj_id = (self._obj_type,) + next(self._id_generator)

        return obj_id

    def set_next_object_color(self):

        color_values = tuple(random.random() * .4 + .5 for i in range(3))
        GD[f"next_{self._obj_type}_color"] = color_values

    def get_next_object_color(self):

        r, g, b = GD[f"next_{self._obj_type}_color"]
        color = VBase4(r, g, b, 1.)

        return color

    def get_origin_pos(self):

        return self._origin_pos

    def add_history(self, toplevel_obj):

        Mgr.do("update_history_time")
        event_descr = f'Create "{toplevel_obj.name}"'
        obj_id = toplevel_obj.id
        obj_data = {obj_id: toplevel_obj.get_data_to_store("creation")}
        event_data = {"objects": obj_data}
        event_data["object_ids"] = set(Mgr.get("object_ids"))
        Mgr.do("add_history", event_descr, event_data, update_time_id=False)

    def __disable_snap(self, reset_grid=False):

        snap_settings = GD["snap"]

        if snap_settings["on"]["creation"]:

            snap_type = f"creation_phase_{self._current_creation_phase}"
            snap_on = snap_settings["on"][snap_type]
            snap_tgt_type = snap_settings["tgt_type"][snap_type]

            if snap_on:
                if snap_tgt_type != "increment":
                    Mgr.do("end_snap_target_checking")
                    Mgr.set_cursor("create")
                if snap_tgt_type == "grid_point" and reset_grid:
                    Mgr.update_app("active_grid_plane", GD["active_grid_plane"])

        snap_settings["type"] = "creation"

    def __end_creation(self, cancel=True):

        self.__disable_snap(reset_grid=True)

        Mgr.remove_task("draw_object")
        process = None

        if cancel or not self._obj.is_valid():

            self._obj.destroy()

        else:

            finalization = self._obj.finalize()

            if finalization:

                def finalize():

                    next(finalization)

                    for step in finalization:
                        yield True

                    obj_type = self._obj_type
                    name = Mgr.get("next_obj_name", obj_type)
                    Mgr.update_remotely("next_obj_name", name)

                    if self._add_to_hist:
                        self.add_history(self._obj.toplevel_obj)

                    yield False

                process = finalize()

            else:

                obj_type = self._obj_type
                name = Mgr.get("next_obj_name", obj_type)
                Mgr.update_remotely("next_obj_name", name)

                if self._has_color:
                    self.set_next_object_color()

                if self._add_to_hist:
                    self.add_history(self._obj.toplevel_obj)

        Mgr.notify("creation_ended")
        Mgr.enter_state("creation_mode")

        if process and next(process):
            Mgr.update_remotely("screenshot", "create")
            descr = f"Creating {self._obj_type}..."
            Mgr.do_gradually(process, "creation", descr, cancellable=True)

        self._obj = None
        self._current_creation_phase = 0
