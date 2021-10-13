from OPEn_gym.envs.utils import BoundedRegion
from base64 import b64encode


class Button(BoundedRegion.BoundedRegion):
    def __init__(self):
        self.command_list = []
        self.object_data = {}
        self.action_func = None
        BoundedRegion.BoundedRegion.__init__(self)

    @staticmethod
    def create_painting(tdw_object, x, z, filename, size={"x": 0.5, "y": 0.5}):
        with open(filename, "rb") as f:
            image = b64encode(f.read()).decode("utf-8")
        painting_id = tdw_object.get_unique_id()
        painting_position = {"x": x, "y": 0.8324, "z": z}
        dimensions = {"x": 1, "y": 1}
        tdw_object.communicate([{"$type": "create_painting",
                                 "position": painting_position,
                                 "size": size,
                                 "euler_angles": {"x": 90, "y": 0, "z": 0},
                                 "id": painting_id},
                                {"$type": "set_painting_texture",
                                 "id": painting_id,
                                 "dimensions": dimensions,
                                 "image": image}
                                ])
        return painting_id

    def create_button(self, tdw_object, button_image, button_size, button_positon):
        self.object_id = self.create_painting(tdw_object, x=button_positon["x"], z=button_positon["z"], filename=button_image,
                        size={"x": button_size, "y": button_size})
        self.bounds["x_left"] = button_positon["x"] - button_size*0.5
        self.bounds["x_right"] = button_positon["x"] + button_size * 0.5
        self.bounds["z_upper"] = button_positon["z"] + button_size * 0.5
        self.bounds["z_lower"] = button_positon["z"] - button_size * 0.5

    def add_object_data(self, object_data):
        self.object_data = object_data

    def is_button_pressed(self, object_information):
        if self.current_state is not None:
            self.previous_state = self.current_state
        self.current_state = self.check_object_bounds(object_information)
        if self.previous_state:
            for to_check_object in self.current_state.keys():
                # Activate the button if the object passed over the button
                if self.previous_state[to_check_object] == "inside" and self.current_state[to_check_object] == "outside":
                    return True
        return False
