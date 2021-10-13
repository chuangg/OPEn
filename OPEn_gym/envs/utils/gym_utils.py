from OPEn_gym.envs.utils import primitives, procedurally_gen_control_tasks, object_configuration
import io
import numpy as np
from tdw.tdw_utils import TDWUtils
import requests
import pandas as pd
import os
import json
from tdw.controller import Controller
from tdw.output_data import Images, OutputData
from PIL import Image as pil_Image
from typing import List, Union
from json import dumps


class TDW_sim(Controller):
    def __init__(self, puzzle_number, port, asset_path, launch_build=True):
        self.objects = None
        self.puzzle_number = puzzle_number
        self.option = {
            "height": 168,
            "width": 168
        }
        # self.option = {
        #     "height": 320,
        #     "width": 320
        # }
        # self.option = {
        #     "height": 640,
        #     "width": 640
        # }
        # self.option = {
        #     "height": 480,
        #     "width": 480
        # }
        self.port = port
        self.asset_path = asset_path
        super().__init__(port=port, launch_build=launch_build)
        self.communicate({"$type": "set_error_handling", "exception": False, "error": False})

        # self.communicate({"$type": "set_network_logging", "value": True})

    # def communicate(self, commands: Union[dict, List[dict]]) -> list:
    #     with io.open(f"log_{self.port}.txt", "at", encoding="utf-8") as f:
    #         f.write(dumps(commands) + "\n")
    #     return super().communicate(commands)

    def run(self, puzzle_type="non-goal", proc_gen=False, debug=True):
        self.start()
        load_scene(self, self.option, debug)

    def take_action(self, action,  last_action_state, skip_frame):
        return take_action(self, self.objects, action, last_action_state, skip_frame)

    def output_images(self, output):
        if output:
            self.communicate({"$type": "send_images",
                                 "frequency": "always"})
        else:
            self.communicate({"$type": "send_images",
                              "frequency": "never"})

    def change_material(self, object_id, color=None):
        object_configs = object_configuration.object_configuration()
        if color:
            resp = self.communicate(
                {"$type": "set_color", "color": color, "id": object_id}, )

            return get_image(resp)
        resp = self.communicate(
            {"$type": "set_color", "color": object_configs.touch_sphere["after_color"], "id": object_id},)
        return get_image(resp)


def get_image(resp):
    for r in resp:
        r_id = OutputData.get_data_type_id(r)
        if r_id == "imag":
            images = Images(r)
            img = np.array(pil_Image.open(io.BytesIO(images.get_image(0)))).astype(np.uint8)
            return img
    print("No image found :(")
    return None


class SceneState:
    def __init__(self):
        self.collision_data = None
        self.collided = False
        self.object_data = None
        self.object_updated = False
        self.image_1 = None
        self.image_2 = None
        self.image_1_ready = False
        self.image_2_ready = False

    def set_collision_data(self, data):
        self.collision_data = data
        self.collided = True

    def set_object_data(self, data):
        self.object_data = data
        self.object_updated = True

    def parse_collision_data(self):
        collider_id = self.collision_data["collider_id"]
        collidee_id = self.collision_data["collidee_id"]
        return collider_id, collidee_id

    def parse_object_data(self):
        return_data = {}
        for objs in self.object_data:
            if "model_name" in objs.keys():
                return_data[objs["id"]] = {
                    "model_name": objs["model_name"],
                    "position": objs["position"],
                    "velocity": objs["velocity"],
                    "rotation": objs["rotation"],
                    "mass": objs["mass"]
                }
        return return_data

scene_state_data = SceneState()


def clear_scene(tdw_object, object_inventory):
    commands = []
    object_configs = object_configuration.object_configuration()

    inv_objs = []
    dragged_objects = []
    for object_cat in ["ad_patch"]:
        for profiles in object_inventory[object_cat]["used"].keys():
            for obj_tuple in object_inventory[object_cat]["used"][profiles]:
                commands.append({"$type": "teleport_painting", "position": obj_tuple[1], "id": obj_tuple[0]})
                object_inventory[object_cat]["not_used"][profiles].append(obj_tuple)
            object_inventory[object_cat]["used"][profiles] = []
    for object_cat in ["cube", "touch_sphere", "high_value_touch_sphere", "wall_pieces", "ramp"]:
        for profiles in object_inventory[object_cat]["used"].keys():
            for obj_tuple in object_inventory[object_cat]["used"][profiles]:
                commands.append({"$type": "teleport_object", "id": obj_tuple[0], "position": obj_tuple[1]})
                # Don't reset orientation of wall pieces
                if object_cat not in ["wall_pieces", "ad_patch", "ramp"]:
                    dragged_objects.append(
                        {"$type": "set_object_drag", "id": obj_tuple[0], "drag": 100, "angular_drag": 100},
                        )
                    commands.append({"$type": "rotate_object_to_euler_angles", "euler_angles": {"x": 0, "y": 0, "z": 0},
                                 "id": obj_tuple[0]})
                if object_cat == "touch_sphere":
                    commands.append({"$type": "set_color", "color": object_configs.touch_sphere["before_color"],
                                     "id": obj_tuple[0]})
                if object_cat == "high_value_touch_sphere":
                    commands.append({"$type": "set_color", "color": object_configs.high_value_touch_sphere["before_color"],
                                     "id": obj_tuple[0]})
                object_inventory[object_cat]["not_used"][profiles].append(obj_tuple)
                inv_objs.append(obj_tuple[0])
            object_inventory[object_cat]["used"][profiles] = []
    commands.extend([{"$type": "rotate_object_to_euler_angles", "euler_angles": {"x": 0, "y": 0, "z": 0},
                      "id": object_inventory["main_sphere"][0]},
                     {"$type": "teleport_object", "id": object_inventory["main_sphere"][0],
                      "position": object_inventory["main_sphere"][1]}
                     ])
    dragged_objects.append({"$type": "set_object_drag", "id": object_inventory["main_sphere"][0], "drag": 100,
                            "angular_drag": 100})
    dragged_objects.append({"$type": "step_physics", "frames": 1})
    un_drag = []
    for cmd in dragged_objects:
        cmd_ = dict(cmd)
        cmd_["drag"] = 0
        cmd_["angular_drag"] = 0
        un_drag.append(cmd_)
    dragged_objects.extend(un_drag)

    inv_objs.append(object_inventory["main_sphere"][0])
    scene_objects = [objs for objs in list(tdw_object["reset_params"].keys()) if objs not in inv_objs]

    # for object_ids in scene_objects + tdw_object["scene_ramps"]:
    #     commands.append({"$type": "destroy_object", "id": object_ids})

    return dragged_objects, commands


def load_scene(tdw_object, options, debug=True):
    if debug:
        tdw_object.communicate(TDWUtils.create_empty_room(24, 24))
    else:
        tdw_object.communicate(TDWUtils.create_empty_room(24, 24))
        # tdw_object.load_streamed_scene(scene="box_room_2018")
        # Load streamed scene.
        # Change the skybox
        sky_box_cmd = tdw_object.get_add_hdri_skybox("furry_clouds_4k")
        # Adjust post-processing settings.
        tdw_object.communicate([sky_box_cmd,
                                {"$type": "set_post_exposure", "post_exposure": 1.25},
                                {"$type": "set_contrast", "contrast": 0},
                                {"$type": "set_saturation", "saturation": 10},
                                {"$type": "set_screen_space_reflections", "enabled": True},
                                {"$type": "set_vignette", "enabled": False}])

        wall_material = "linen_burlap_irregular"
        primitives.create_offline_material(tdw_object, wall_material)
        tdw_object.communicate([
            {"$type": "set_proc_gen_floor_material", "name": wall_material},
            {"$type": "set_proc_gen_floor_texture_scale", "scale": {"x": 8, "y": 8}}
        ])

        # Set the shadow strength to maximum.
        tdw_object.communicate({"$type": "set_shadow_strength", "strength": 1.0})

    # set screen size
    tdw_object.communicate({"$type": "set_screen_size", "height": options["height"], "width": options["width"]})
    print("Base scene loaded")


def load_initial_objects(tdw_object, top_down_camera=False):
    tdw_object.communicate({"$type": "create_avatar",
                            "type": "A_Img_Caps_Kinematic",
                            "id": "uniqueid1"})
    tdw_object.communicate({"$type": "set_target_framerate", "framerate": 60})
    add_audio_sensor(tdw_object)
    scene_object_ids = []
    if top_down_camera:
        tdw_object.communicate({"$type": "teleport_avatar_to", "avatar_id": "uniqueid1", "env_id": 0,
                                "position": {"x": 3.39, "y": 7, "z": -6.3}}) # {"x": 0.0, "y": 3.2, "z": 0.01}
        tdw_object.communicate({"$type": "rotate_avatar_to_euler_angles", "avatar_id": "uniqueid1", "env_id": 0,
                                "euler_angles": {"x": 90, "y": 0, "z": 0}})
        scene_object_ids.append(0)
    else:
        tdw_object.communicate({"$type": "teleport_avatar_to", "avatar_id": "uniqueid1", "env_id": 0,
                                "position": {"x": -0.538, "y": 2.072, "z": -1.767}})

        tdw_object.communicate({"$type": "rotate_avatar_to_euler_angles", "avatar_id": "uniqueid1", "env_id": 0,
                                "euler_angles": {"x": 43.376, "y": 25.489, "z": 1.481}})

    tdw_object.communicate({"$type": "set_pass_masks", "avatar_id": "uniqueid1", "pass_masks": ["_img"]})
    table_top_material = "plastic_vinyl_glossy_green"
    create_base_table(tdw_object, table_top_material, scene_object_ids)
    return scene_object_ids


def create_base_table(tdw_object, table_top_material, scene_object_ids):
    table_center = (0, 0)
    table = primitives.create_offline_model(tdw_object, {"x": 0, "y": 0.0, "z": 0}, {"x": 0.0, "y": 0.0, "z": 0.0},
                                            "quatre_dining_table")
    scene_object_ids.append(table)
    primitives.create_offline_material(tdw_object, table_top_material)
    tdw_object.communicate([
        {"$type": "scale_object", "id": table, "scale_factor": {"x": 1.09, "y": 0.955, "z": 0.995}},
        {"$type": "set_visual_material", "id": table, "material_name": table_top_material,
         "object_name": "Quatre_Dining_Table_47",
         "material_index": 0},
        {"$type": "set_visual_material", "id": table, "material_name": table_top_material,
         "object_name": "Quatre_Dining_Table_47",
         "material_index": 1},
        {"$type": "set_visual_material", "id": table, "material_name": table_top_material,
         "object_name": "Quatre_Dining_Table_1",
         "material_index": 0},
        {"$type": "set_kinematic_state", "id": table, "is_kinematic": True, "use_gravity": False}
    ])

    wall_color = {"r": 70/255, "g": 65/255, "b": 89/255, "a": 0.0}
    wall_ids = [

    primitives.thin_wall(tdw_object, {"x": table_center[0] , "y": 0.8749, "z": table_center[1] - 1.1218},
                         {"x": 0.0, "y": 90.0, "z": 0.0}, scale={"x": 0.01, "y": 0.1, "z": 1.09}, color=wall_color),
    primitives.thin_wall(tdw_object, {"x": table_center[0], "y": 0.8749, "z": table_center[1] + 1.1218},
                         {"x": 0.0, "y": 90.0, "z": 0.0}, scale={"x": 0.01, "y": 0.1, "z": 1.09}, color=wall_color),

    primitives.thin_wall(tdw_object, {"x": table_center[0] + 0.641, "y": 0.8749, "z": table_center[1]},
                         {"x": 0.0, "y": 0.0, "z": 0.0}, scale={"x": 0.01, "y": 0.1, "z": 2.05}, color=wall_color),
    primitives.thin_wall(tdw_object, {"x": table_center[0] - 0.641, "y": 0.8749, "z": table_center[1]},
                         {"x": 0.0, "y": 0.0, "z": 0.0}, scale={"x": 0.01, "y": 0.1, "z": 2.05}, color=wall_color)
    ]
    scene_object_ids.extend(wall_ids)
    table_center = (0, 0)
    # Create four corner walls
    corner_material = "metal_grid_rounded_patterned"
    wall_ids = [
    primitives.thin_wall(tdw_object, {"x": table_center[0] - 0.589, "y": 0.8749, "z": table_center[1] - 1.0725},
                         {"x": 0.0, "y": -45.0, "z": 0.0}, color=wall_color),
    primitives.thin_wall(tdw_object, {"x": table_center[0] + 0.589, "y": 0.8749, "z": table_center[1] - 1.0725},
                         {"x": 0.0, "y": 45.0, "z": 0.0}, color=wall_color),
    primitives.thin_wall(tdw_object, {"x": table_center[0] + 0.589, "y": 0.8749, "z": table_center[1] + 1.0725},
                         {"x": 0.0, "y": -45.0, "z": 0.0}, color=wall_color),
    primitives.thin_wall(tdw_object, {"x": table_center[0] - 0.589, "y": 0.8749, "z": table_center[1] + 1.0725},
                         {"x": 0.0, "y": 45.0, "z": 0.0}, color=wall_color)
        ]
    print("Initial Objects loaded")
    scene_object_ids.extend(wall_ids)
    return table


def setup_tdw_instance(tdw_ip, self_ip, port, audio_dir):
    url = "http://{}:5000/get_tdw".format(tdw_ip)
    # if port is None:
    #     available_port = get_port()
    # else:
    #     available_port = port
    data = {
        'ip_address': self_ip,
        'port': int(port)
    }
    if audio_dir is not None:
        data["audio_dir"] = audio_dir
    response = requests.post(url, json=json.dumps(data))
    print(response.status_code, response.reason)
    docker_id = response.json()['docker_id']
    return docker_id


def get_port():
    if os.path.isfile("available_ports.csv"):
        available_ports = pd.read_csv("available_ports.csv")
    else:
        print("Port tracking file doesn't exist. Creating one..")
        available_ports = pd.DataFrame(columns=["port", "status"])
        no_ports = 100
        port_start = 1071
        for i in range(no_ports):
            available_ports.loc[i] = [port_start, "free"]
            port_start += 1
    available_port_ = None
    for i in range(available_ports.shape[0]):
        if available_ports['status'].iloc[i] == "free":
            available_port_ = available_ports["port"].iloc[i]
            available_ports["status"].iloc[i] = "not-free"
            break
    if not available_port_:
        raise Exception("No port available")
    available_ports.to_csv("available_ports.csv", index=False)
    return available_port_


def kill_tdw(tdw_ip, docker_id):
    url = "http://{}:5000/kill_tdw".format(tdw_ip)
    data = {
        "container_id": docker_id
    }
    response = requests.post(url, json=json.dumps(data))
    print(response.status_code, response.reason)


def load_puzzle_proc_gen(tdw_object, puzzle_data, object_inventory, inventory_ids):
    objects, puzzle_type, object_inventory = procedurally_gen_control_tasks.render_puzzle(tdw_object, puzzle_data, object_inventory, inventory_ids)
    return objects, puzzle_type, object_inventory


def add_audio_sensor(tdw_object):
    tdw_object.communicate([{"$type": "add_audio_sensor",
                      "avatar_id": "uniqueid1"},
                     {"$type": "set_target_framerate",
                      "framerate": 60},
                     {"$type": "set_post_process",
                      "value": True},
                     {"$type": "set_focus_distance",
                      "focus_distance": 2},
                     {"$type": "set_render_quality",
                      "render_quality": 5}])


def take_action(tdw_object, objects, actions, last_action_state, skip_frame):

    if actions == 0:
        if skip_frame:
            resp = tdw_object.communicate({"$type": "step_physics", "frames": 0})
        else:
            commands = [{"$type": "step_physics", "frames": 0}]
            # If this was last step of the action than stop it
            if last_action_state["steps"] == 1:
                commands.extend(stop_object(objects["sphere"]))
            # If this was not end of action then reduce it
            if last_action_state["steps"] > 0:
                last_action_state["steps"] -= 1
            resp = tdw_object.communicate(commands)
        return resp, last_action_state

    force_time_steps = 4
    direction = {
        1: (1, 0),
        2: (1, 1),
        3: (0, 1),
        4: (-1, 1),
        5: (-1, 0),
        6: (-1, -1),
        7: (0, -1),
        8: (1, -1)
    }
    selected_direction = direction[actions]
    commands = []
    if skip_frame:
        # Apply force on agent
        commands.extend(apply_force_to_object(objects["sphere"], selected_direction))
        last_action_state = {
            "action": actions,
            "steps": 0
        }
        # Step physics by "force_time_steps" steps
        commands.append({"$type": "step_physics", "frames": force_time_steps})
        # Apply drag, step 1 physics step to take effect and then remove the drag
        commands.extend(stop_object(objects["sphere"]))
    else:
        # Check if last time step is 0, if so apply new action, else step physics
        if last_action_state["steps"] == 0:
            commands.extend(apply_force_to_object(objects["sphere"], selected_direction))
            last_action_state = {
                "action": actions,
                "steps": force_time_steps - 1
            }
        else:
            commands.append({"$type": "step_physics", "frames": 1})
            last_action_state["steps"] -= 1
            # If this was last step then stop the object
            if last_action_state["steps"] == 0:
                commands.extend(stop_object(objects["sphere"]))
    resp = tdw_object.communicate(commands)
    return resp, last_action_state


def apply_force_to_object(obj_id, selected_direction):
    magnitude = 25
    return [
        {"$type": "apply_force_to_object",
         "force": {"x": selected_direction[0] * magnitude,
                   "y": 0,
                   "z": selected_direction[1] * magnitude},
         "id": obj_id}]


def stop_object(obj_id):
    high_drag, low_drag, high_angular_drag, low_angular_drag = 100, 0, 100, 0
    commands = []
    commands.append({"$type": "set_object_drag", "id": obj_id, "drag": high_drag,
                     "angular_drag": high_angular_drag})
    commands.append({"$type": "step_physics", "frames": 1})
    commands.append({"$type": "set_object_drag", "id": obj_id, "drag": low_drag,
                     "angular_drag": low_angular_drag})
    return commands


def reset_scene(tdw_object, objects):
    reset_params = objects["reset_params"]
    commands = []
    object_configs = object_configuration.object_configuration()
    dragged_objects = []
    for object_id in reset_params.keys():
        dragged_objects.append({"$type": "set_object_drag", "id": object_id, "drag": 100, "angular_drag": 100})
        # Check if object is a lever and reset the position and orientation
        if "position" in reset_params[object_id].keys() and "rotation" in reset_params[object_id].keys():
            commands.extend([
                             {"$type": "rotate_object_to_euler_angles", "euler_angles": reset_params[object_id]["rotation"],
                              "id": object_id},
                             {"$type": "teleport_object", "id": object_id,
                              "position": reset_params[object_id]["position"]}
                             ])
        # Check if object is target sphere then reset and color and reset position and
        # default the orientation to {"x": 0, "y": 0, "z": 0}
        elif object_id in objects["target_spheres"]:
            commands.extend([
                {"$type": "rotate_object_to_euler_angles", "euler_angles": {"x": 0, "y": 0, "z": 0},  "id": object_id},
                {"$type": "teleport_object", "id": object_id, "position": reset_params[object_id]},
                {"$type": "set_color", "color": object_configs.touch_sphere["before_color"], "id": object_id},
            ])
        elif object_id in objects["high_value_target"]:
            commands.extend([
                {"$type": "rotate_object_to_euler_angles", "euler_angles": {"x": 0, "y": 0, "z": 0}, "id": object_id},
                {"$type": "teleport_object", "id": object_id, "position": reset_params[object_id]},
                {"$type": "set_color", "color": object_configs.high_value_touch_sphere["before_color"], "id": object_id},
            ])
        elif object_id in objects["push_spheres"]:
            commands.extend([
                {"$type": "rotate_object_to_euler_angles", "euler_angles": {"x": 0, "y": 0, "z": 0}, "id": object_id},
                {"$type": "teleport_object", "id": object_id, "position": reset_params[object_id]},
                {"$type": "set_color", "color": object_configs.push_sphere["before_color"], "id": object_id}
            ])
        # For everything else just reset position and default the orientation to {"x": 0, "y": 0, "z": 0}
        else:
            commands.extend([
                                {"$type": "rotate_object_to_euler_angles", "euler_angles": {"x": 0, "y": 0, "z": 0},
                                 "id": object_id},
                                {"$type": "teleport_object", "id": object_id,
                                 "position": reset_params[object_id]}
                                ])

    dragged_objects.append({"$type": "step_physics", "frames": 1})
    un_drag = []
    for cmd in dragged_objects:
        cmd_ = dict(cmd)
        cmd_["drag"] = 0
        cmd_["angular_drag"] = 0
        un_drag.append(cmd_)
    dragged_objects.extend(un_drag)
    tdw_object.communicate(dragged_objects)
    tdw_object.communicate(commands)
    # Reset ramp
    reset_factor = 1
    for button in objects["buttons"]:
        reset_factor *= button.reset_param
        button.reset_param = 1
    if "main_ramp" in objects:
        main_ramp = objects["main_ramp"]
        tdw_object.communicate(
            {"$type": "scale_object", "id": main_ramp, "scale_factor": {"x": 1, "y": reset_factor, "z": 1}})

