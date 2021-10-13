
class BoundedRegion:
    def __init__(self):
        self.object_id = None
        self.check_objects = []
        self.bounds = {
            "x_left": 0.0,
            "x_right": 0.0,
            "z_upper": 0.0,
            "z_lower": 0.0
        }
        self.current_state = None
        self.previous_state = None

    def check_object_bounds(self, object_information):
        """
        Check the objects in the check_object list are inside the bounds of this region
        :param object_information:
        :return:
        """
        result = {}
        for obj in self.check_objects:
            if obj not in object_information:
                print(f"{obj} was not found in object information")
            else:
                object_position = object_information[obj]["position"]
                if (self.bounds["x_left"] < object_position[0] < self.bounds["x_right"]) and \
                    (self.bounds["z_lower"] < object_position[2] < self.bounds["z_upper"]):
                    result[obj] = "inside"
                else:
                    result[obj] = "outside"

        return result

    def add_check_object(self, check_objects):
        self.check_objects.extend(check_objects)
