
class object_configuration:
    def __init__(self):
        self.cube_1 = {
            "mass": 10.0,
            "color_id": 1
        }
        self.cube_2 = {
            "mass": 5.0,
            "color_id": 2
        }
        self.main_sphere = {
            "color_id": 3
        }
        self.push_sphere = {
            "before_color_id": 4,
            "before_material": "plaster_cellulose_insulation",
            "after_color_id": 5,
            "after_material": "metallic_car_paint",
            "before_color": {"r": 243 / 255, "g": 220 / 255, "b": 173 / 255, "a": 1.0},
            "after_color": {"r": 139 / 255, "g": 47 / 255, "b": 151 / 255, "a": 1.0},

        }
        self.touch_sphere = {
            "before_color_id": 6,
            "before_material": "plastic_vinyl_glossy_yellow",
            # "before_color": {"r": 253 / 255, "g": 95 / 255, "b": 0 / 255, "a": 1.0},
            "before_color" : {"r": 247 / 255, "g": 183 / 255, "b": 29 / 255, "a": 1.0},
            "after_color": {"r": 0 / 255, "g": 189 / 255, "b": 170 / 255, "a": 1.0},
            "after_color_id": 7,
            "after_material": "plastic_hammered"
        }
        self.high_value_touch_sphere = {
            "before_color_id": 8,
            "before_color": {"r": 118 / 255, "g": 162 / 255, "b": 30 / 255, "a": 1.0},
            "after_color": {"r": 83 / 255, "g": 90 / 255, "b": 59 / 255, "a": 1.0},
            "after_color_id": 9,
        }
        self.rectangle = {
            "before_color" : {"r": 91 / 255, "g": 140 / 255, "b": 133 / 255, "a": 1.0}
        }
