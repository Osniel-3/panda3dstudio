from ..base import *


class FileButtons(object):

    def __init__(self):

        self._filename = ""

        handlers = {
            "new": self.__reset_scene,
            "open": self.__load_scene,
            "save": self.__save_scene,
            "save_as": self.__save_scene_as,
            "export": self.__export_scene,
            "import": self.__import_scene,
        }

        for file_op in ("new", "open", "save", "save_as", "export", "import"):

            btn_id = "file_%s" % file_op
            label = file_op.replace("_", " ").title()
            icon_path = os.path.join(GFX_PATH, "icon_" + file_op + ".png")
            btn_props = (label, icon_path)

            Mgr.do("add_deepshelf_btn", btn_id, btn_props, handlers[file_op])

        Mgr.add_app_updater("unsaved_scene", self.__set_scene_as_unsaved)

    def __reset_scene(self):

        if Mgr.get_global("unsaved_scene"):

            answer = wx.MessageBox("Save changes to current scene before resetting?",
                                   "Save changes",
                                   wx.YES_NO | wx.CANCEL | wx.ICON_EXCLAMATION)

            if Mgr.get_global("ctrl_down"):
                Mgr.set_global("ctrl_down", False)

            if answer == wx.YES:
                if not self.__save_scene():
                    return
            elif answer == wx.CANCEL:
                return

        Mgr.update_app("scene", "reset")
        self._filename = ""
        Mgr.do("set_scene_label", "New")

    def __load_scene(self):

        if Mgr.get_global("unsaved_scene"):

            answer = wx.MessageBox("Save changes to current scene before loading?",
                                   "Save changes",
                                   wx.YES_NO | wx.CANCEL | wx.ICON_EXCLAMATION)  # , self)

            if answer == wx.YES:
                self.__save_scene()
            elif answer == wx.CANCEL:
                return

        filename = wx.FileSelector("Open scene",
                                   "", "", "p3ds", "*.p3ds",
                                   wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if filename:
            Mgr.update_app("scene", "load", filename)
            self._filename = filename
            Mgr.do("set_scene_label", self._filename)

        if Mgr.get_global("ctrl_down"):
            Mgr.set_global("ctrl_down", False)

    def __save_scene(self):

        if self._filename:

            Mgr.update_app("scene", "save", self._filename)
            Mgr.do("set_scene_label", self._filename)

            if Mgr.get_global("ctrl_down"):
                Mgr.set_global("ctrl_down", False)

            return True

        return self.__save_scene_as()

    def __save_scene_as(self):

        filename = wx.FileSelector("Save scene as",
                                   "", "", "p3ds", "*.p3ds",
                                   wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if Mgr.get_global("ctrl_down"):
            Mgr.set_global("ctrl_down", False)

        if filename:
            Mgr.update_app("scene", "save", filename)
            self._filename = filename
            Mgr.do("set_scene_label", self._filename)
            return True

        return False

    def __set_scene_as_unsaved(self):

        scene_label = (self._filename if self._filename else "New")

        if Mgr.get_global("unsaved_scene"):
            scene_label += "*"

        Mgr.do("set_scene_label", scene_label)

    def __export_scene(self):

        filename = wx.FileSelector("Export scene",
                                   "", "", "bam", "*.bam",
                                   wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if Mgr.get_global("ctrl_down"):
            Mgr.set_global("ctrl_down", False)

        if filename:
            Mgr.update_app("scene", "export", filename)

    def __import_scene(self):

        filename = wx.FileSelector("Import scene",
                                   "", "", "bam", "*.bam",
                                   wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if Mgr.get_global("ctrl_down"):
            Mgr.set_global("ctrl_down", False)

        if filename:
            Mgr.update_app("scene", "import", filename)
            self.__set_scene_as_unsaved()

        if Mgr.get_global("ctrl_down"):
            Mgr.set_global("ctrl_down", False)