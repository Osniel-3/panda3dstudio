from .base import *


class RadioButton(Widget):

    _bullet = None
    _box_size = (0, 0)

    @classmethod
    def init(cls):

        gfx_id = Skin.atlas.gfx_ids["bullet"][""][0][0]
        x, y, w, h = Skin.atlas.regions[gfx_id]
        cls._bullet = img = PNMImage(w, h, 4)
        img.copy_sub_image(Skin.atlas.image, 0, 0, x, y, w, h)

        options = Skin.options
        cls._box_size = (options["radiobox_width"], options["radiobox_height"])

    def __init__(self, parent, btn_id, text, group):

        container_type = parent.root_container.widget_type

        Widget.__init__(self, container_type + "_radiobutton", parent, gfx_ids={})

        self.id = btn_id
        self.group = group
        self._is_clicked = False
        self._is_selected = False
        self._command = lambda: None
        self._text = text

        widget_type = container_type + "_radiobutton"
        skin_text = Skin.text[widget_type]
        font = skin_text["font"]
        color = skin_text["color"]
        self._label = label = font.create_image(text, color)
        color = Skin.colors[f"disabled_{widget_type}_text"]
        self._label_disabled = font.create_image(text, color)

        gfx_id = Skin.atlas.gfx_ids["radiobox"][container_type][0][0]
        x, y, w, h = Skin.atlas.regions[gfx_id]
        l, _, b, t = self._btn_borders
        w_l, h_l = label.size
        w += group.get_text_offset() + w_l - l
        h = max(h - b - t, h_l)
        self.set_size((w, h), is_min=True)

        if "\n" in text:
            l, _, b, t = Skin.atlas.outer_borders[container_type + "_radiobox"]
            font = Skin.text[container_type + "_radiobutton"]["font"]
            h_f = font.get_height() * (text.count("\n") + 1)
            h = Skin.options["radiobox_height"]
            dh = max(0, h_f - h) // 2
            b = max(0, b - dh)
            t = max(0, t - dh)
            btn_borders = (l, 0, b, t)
            img_offset = (-l, -t)
        else:
            btn_borders = self._btn_borders
            img_offset = self._img_offset

        self.outer_borders = btn_borders
        self.image_offset = img_offset

    def destroy(self):

        if Widget.destroy(self):
            self.group.destroy()
            self.group = None
            self._command = lambda: None

    def set_text(self, text):

        if self._text == text:
            return False

        self._text = text
        container_type = self.root_container.widget_type
        widget_type = container_type + "_radiobutton"
        skin_text = Skin.text[widget_type]
        font = skin_text["font"]
        color = skin_text["color"]
        self._label = label = font.create_image(text, color)
        color = Skin.colors[f"disabled_{widget_type}_text"]
        self._label_disabled = font.create_image(text, color)

        gfx_id = Skin.atlas.gfx_ids["radiobox"][container_type][0][0]
        x, y, w, h = Skin.atlas.regions[gfx_id]
        l, _, b, t = self._btn_borders
        w_l, h_l = label.size
        w += self.group.get_text_offset() + w_l - l
        h = max(h - b - t, h_l)
        self.set_size((w, h), is_min=True)

        if "\n" in text:
            l, _, b, t = Skin.atlas.outer_borders[container_type + "_radiobox"]
            font = Skin.text[container_type + "_radiobutton"]["font"]
            h_f = font.get_height() * (text.count("\n") + 1)
            h = Skin.options["radiobox_height"]
            dh = max(0, h_f - h) // 2
            b = max(0, b - dh)
            t = max(0, t - dh)
            btn_borders = (l, 0, b, t)
            img_offset = (-l, -t)
        else:
            btn_borders = self._btn_borders
            img_offset = self._img_offset

        self.outer_borders = btn_borders
        self.image_offset = img_offset

        return True

    def update_text_offset(self, old_text_offset, new_text_offset):

        w, h = self.get_size()
        w += new_text_offset - old_text_offset
        self.set_size((w, h), is_min=True)

    def __card_update_task(self):

        if self.is_hidden():
            return

        image = self.get_image(composed=False)
        parent = self.parent

        if not (image and parent):
            return

        x, y = self.get_pos()
        w, h = self.get_size()
        img_offset_x, img_offset_y = self.image_offset
        w -= img_offset_x
        h -= img_offset_y
        x += img_offset_x
        y += img_offset_y
        img = PNMImage(w, h, 4)
        parent_img = parent.get_image(composed=False)

        if parent_img:
            img.copy_sub_image(parent_img, 0, 0, x, y, w, h)

        img.blend_sub_image(image, 0, 0, 0, 0)
        self.card.copy_sub_image(self, img, w, h, img_offset_x, img_offset_y)

    def __update_card_image(self):

        task = self.__card_update_task

        if self.group.is_card_update_delayed():
            task_id = "update_card_image"
            PendingTasks.add(task, task_id, sort=1, id_prefix=self.widget_id,
                             batch_id="widget_card_update")
        else:
            task()

    def update_images(self, recurse=True, size=None):

        self._images = {"": self._base_img}

        return self._images

    def create_base_image(self):

        border_image = self.get_border_image()
        w_b, h_b = border_image.size
        label = self._label
        w_l, h_l = label.size
        x_l = w_b + self.group.get_text_offset()
        w = x_l + w_l
        h = max(h_b, h_l)
        y_l = (h - h_l) // 2
        y_b = (h - h_b) // 2
        self._label_pos = (x_l, y_l)
        img_offset_x, img_offset_y = self.get_box_image_offset()
        self._box_pos = (-img_offset_x, y_b - img_offset_y)
        self._base_img = img = PNMImage(w, h, 4)
        box_img = PNMImage(*self._box_size, 4)
        r, g, b, a = self.group.get_back_color()
        box_img.fill(r, g, b)
        box_img.alpha_fill(a)
        img.copy_sub_image(box_img, *self._box_pos, 0, 0)
        img.blend_sub_image(border_image, 0, y_b, 0, 0)

    def get_image(self, state=None, composed=True):

        image = Widget.get_image(self, state, composed)

        if not image:
            return

        img = PNMImage(image)

        if not self.is_enabled():
            label = self._label_disabled
        else:
            label = self._label

        img.copy_sub_image(label, *self._label_pos, 0, 0)

        if self._is_selected:
            w, h = self._box_size
            bullet = PNMImage(self._bullet) * self.group.get_bullet_color()
            w_b, h_b = bullet.size
            x, y = self._box_pos
            x += (w - w_b) // 2
            y += (h - h_b) // 2
            img.blend_sub_image(bullet, x, y, 0, 0)

        return img

    def update(self):

        self._images = {"": self._base_img}
        self.__update_card_image()

    def on_leave(self):

        self._is_clicked = False

    def on_left_down(self):

        self._is_clicked = True

    def on_left_up(self):

        if self._is_clicked:

            if not self._is_selected:
                self.group.set_selected_button(self.id)
                self._command()
                self.__update_card_image()

            self._is_clicked = False

    @property
    def command(self):

        return self._command

    @command.setter
    def command(self, command):

        self._command = command if command else lambda: None

    def set_selected(self, is_selected=True):

        if self._is_selected == is_selected:
            return

        self._is_selected = is_selected
        self.__update_card_image()

    def enable(self, enable=True, check_group_disablers=True):

        if enable and not self.always_enabled and check_group_disablers:
            for disabler in self.group.get_disablers().values():
                if disabler():
                    return False

        if not Widget.enable(self, enable):
            return False

        if not self.is_hidden():
            self.__update_card_image()


class RadioButtonGroup:

    def __init__(self, bullet_color, back_color, prim_dir, prim_limit=0,
                 gaps=(0, 0), expand=False, text_offset=0):

        self._btns = {}
        self._selected_btn_id = None
        self._delay_card_update = False
        self._is_enabled = True
        self._disablers = {}
        self._default_bullet_color = self._bullet_color = bullet_color
        self._default_back_color = self._back_color = back_color
        self._text_offset = text_offset
        self._expand = expand
        self._sizer = Sizer(prim_dir, prim_limit, gaps)

        if expand:
            kwargs = {("row" if prim_dir == "vertical" else "column") + "_proportion": 1.}
            self._sizer.set_default_proportions(0., 0.)
            self._sizer.set_default_proportions(**kwargs)

    def destroy(self):

        if not self._btns:
            return

        self._btns.clear()
        self._disablers.clear()

    @property
    def sizer(self):

        return self._sizer

    def __update_proportions(self):

        s = self._sizer
        s.set_default_proportions(0., 0.)
        kwargs = {("row" if s.prim_dir == "vertical" else "column") + "_proportion": 1.}
        s.set_default_proportions(**kwargs)

    @property
    def prim_dir(self):

        return self._sizer.prim_dir

    @prim_dir.setter
    def prim_dir(self, prim_dir):

        if self._sizer.prim_dir == prim_dir:
            return

        self._sizer.prim_dir = prim_dir

        if self._expand:
            self.__update_proportions()

    @property
    def prim_limit(self):

        return self._sizer.prim_limit

    @prim_limit.setter
    def prim_limit(self, prim_limit):

        if self._sizer.prim_limit == prim_limit:
            return

        self._sizer.prim_limit = prim_limit

        if self._expand:
            self.__update_proportions()

    def delay_card_update(self, delay=True):

        self._delay_card_update = delay

    def is_card_update_delayed(self):

        return self._delay_card_update

    def add_button(self, btn_id, button, index=None):

        self._btns[btn_id] = button
        self._sizer.add(button, alignments=("min", "center"), index=index)

    def remove_button(self, btn_id):

        del self._btns[btn_id]

    def get_button_count(self):

        return len(self._btns)

    def set_selected_button(self, btn_id=None):

        if self._selected_btn_id == btn_id:
            return

        if self._selected_btn_id is not None:
            self._btns[self._selected_btn_id].set_selected(False)

        self._selected_btn_id = btn_id

        if btn_id is not None:
            self._btns[btn_id].set_selected()

    def get_selected_button(self):

        return self._selected_btn_id

    def set_button_command(self, btn_id, command):

        self._btns[btn_id].command = command

    def set_bullet_color(self, color=None, update=False):

        bullet_color = color if color else self._default_bullet_color

        if self._bullet_color != bullet_color:

            self._bullet_color = bullet_color

            if update and self._selected_btn_id:
                self._btns[self._selected_btn_id].update()

    def get_bullet_color(self):

        return self._bullet_color

    def set_back_color(self, color=None, update=False):

        back_color = color if color else self._default_back_color

        if self._back_color != back_color:

            self._back_color = back_color

            if update:
                for btn in self._btns.values():
                    btn.create_base_image()
                    btn.update()

    def get_back_color(self):

        return self._back_color

    def get_text_offset(self):

        return self._text_offset

    def set_text_offset(self, text_offset):

        if self._text_offset == text_offset:
            return False

        prev_text_offset, self._text_offset = self._text_offset, text_offset

        for btn in self._btns.values():
            btn.update_text_offset(prev_text_offset, text_offset)
            btn.create_base_image()

        return True

    def expand(self, expand=True):

        if self._expand == expand:
            return False

        if expand:
            self.__update_proportions()
        else:
            self._sizer.set_default_proportions(0., 0.)

        self._expand = expand

        return True

    def add_disabler(self, disabler_id, disabler):

        self._disablers[disabler_id] = disabler

    def remove_disabler(self, disabler_id):

        del self._disablers[disabler_id]

    def get_disablers(self):

        return self._disablers

    def enable(self, enable=True):

        if self._is_enabled == enable:
            return

        self._is_enabled = enable

        if enable:
            for disabler in self._disablers.values():
                if disabler():
                    return

        for btn in self._btns.values():
            btn.enable(enable)
