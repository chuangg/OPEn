from OPEn_gym.envs.utils.aux_utils import teleport_object, step_one_frame, teleport_object_cmd
from OPEn_gym.envs.utils import Button, object_configuration
from base64 import b64encode
import random
import pkg_resources
import os
import sys

global_object_creator = {"x": -7.504, "y": 3, "z": -5.012}
global_ptr = 0
global_list = [0,1,2,1,0,0,0,0,0,2,1,0,2,1,0,1,0,1,0,2,1,0,2,0,0,2,1,1,0,2,1,0,1]
object_configs = object_configuration.object_configuration()


def create_highlight(tdw_object, x, z):
    file_name = pkg_resources.resource_filename(__name__, 'data/green.png')
    with open(file_name, "rb") as f:
        image = b64encode(f.read()).decode("utf-8")
    painting_id = tdw_object.get_unique_id()
    painting_position = {"x": x, "y": 0.8324, "z": z}
    dimensions = {"x": 1, "y": 1}
    tdw_object.communicate([{"$type": "create_painting",
                             "position": painting_position,
                             "size": {"x": 0.5, "y": 0.5},
                             "euler_angles": {"x": 90, "y": 0, "z": 0},
                             "id": painting_id},
                            {"$type": "set_painting_texture",
                             "id": painting_id,
                             "dimensions": dimensions,
                             "image": image}
                            ])
    return painting_id


def create_goal_with_wall(tdw_object, x, z, enable_wall, highlight=False):
    if highlight:
        area_id = create_highlight(tdw_object, x, z)
        highlighted_areas = {}
        highlighted_areas[area_id] = "data"
    else:
        highlighted_areas = None

    diff = 0.2388
    boundaries = {
        "z_top": z + diff,
        "z_bottom": z - diff,
        "x_left": x - diff,
        "x_right": x + diff
    }
    return highlighted_areas, boundaries


def create_ramp(tdw_object, pos, rot={"x": 0, "y": 90, "z": 0}, object_inventory={}):
    global global_object_creator, global_ptr
    global_object_creator["x"] = global_object_creator["x"] - 1.1
    # Create ramp increase decrease buttons
    if rot["y"] == 270:
        pos["x"] += 0.096
    elif rot["y"] == 90:
        pos["x"] -= 0.096

    ramp_tuple = object_inventory["ramp"]["not_used"][0].pop(0)
    object_inventory["ramp"]["used"][0].append(ramp_tuple)
    ramp = ramp_tuple[0]
    tdw_object.communicate([
        {"$type": "teleport_object", "id": ramp, "position": pos},
        {"$type": "rotate_object_to_euler_angles", "euler_angles": rot, "id": ramp}
    ])
    # If the ramp is changeable than create two button
    return ramp, None, None


def create_wall_piece(tdw_object, wall_orientation, tele_pos, object_inventory):
    def _create_wall_piece(wall_profile, tele_pos):
        available_wall_pieces = object_inventory["wall_pieces"]["not_used"][wall_profile]
        wall_id, wall_original_pos = available_wall_pieces.pop(random.randint(0, len(available_wall_pieces) - 1))
        object_inventory["wall_pieces"]["used"][wall_profile].append((wall_id, wall_original_pos))
        tdw_object.communicate({"$type": "teleport_object", "id": wall_id, "position": tele_pos})
        return wall_id
    corner_diff = 0.036
    if wall_orientation == "h":
        return _create_wall_piece(wall_orientation, tele_pos)
    elif wall_orientation == "v":
        return _create_wall_piece(wall_orientation, tele_pos)
    elif wall_orientation == "c1":
        # {"x": 0.105, "y": 0.1, "z":0.01}
        _pos1 = {"x": tele_pos["x"] + corner_diff, "y": tele_pos["y"], "z": tele_pos["z"] - corner_diff}
        return _create_wall_piece(wall_orientation, _pos1)

    elif wall_orientation == "c2":
        _pos1 = {"x": tele_pos["x"] - corner_diff, "y": tele_pos["y"], "z": tele_pos["z"] - corner_diff}
        return _create_wall_piece(wall_orientation, _pos1)

    elif wall_orientation == "c3":
        _pos1 = {"x": tele_pos["x"] + corner_diff, "y": tele_pos["y"], "z": tele_pos["z"] + corner_diff}
        return _create_wall_piece(wall_orientation, _pos1)

    elif wall_orientation == "c4":
        _pos1 = {"x": tele_pos["x"] - corner_diff, "y": tele_pos["y"], "z": tele_pos["z"] + corner_diff}
        return _create_wall_piece(wall_orientation, _pos1)
    elif wall_orientation == "vb":
        _pos1 = {"x": tele_pos["x"], "y": tele_pos["y"], "z": tele_pos["z"] + corner_diff}
        return _create_wall_piece(wall_orientation, _pos1)
    elif wall_orientation == "vt":
        _pos1 = {"x": tele_pos["x"], "y": tele_pos["y"], "z": tele_pos["z"] - corner_diff}
        return _create_wall_piece(wall_orientation, _pos1)
    elif wall_orientation == "hr":
        _pos1 = {"x": tele_pos["x"] - corner_diff, "y": tele_pos["y"], "z": tele_pos["z"]}
        return _create_wall_piece(wall_orientation, _pos1)
    elif wall_orientation == "hl":
        _pos1 = {"x": tele_pos["x"] + corner_diff, "y": tele_pos["y"], "z": tele_pos["z"]}
        return _create_wall_piece(wall_orientation, _pos1)


def thin_wall(tdw_object, tele_pos, rot={"x": 0, "y": 0, "z": 0}, scale={"x": 0.01, "y": 0.1, "z": 0.141}, wall_material=None, color=None):
    global global_object_creator
    pos = {"x": global_object_creator["x"],
           "y": global_object_creator["y"],
           "z": global_object_creator["z"]}
    global_object_creator["x"] -= 1.1
    # wall_id = tdw_object.add_object("prim_cube", position=pos, rotation=rot, library="models_special.json")
    wall_id = create_offline_model(tdw_object, position=pos, rotation=rot, model_name="prim_cube")
    commands = [
        {"$type": "scale_object", "id": wall_id, "scale_factor": scale},
        {"$type": "set_kinematic_state", "id": wall_id, "is_kinematic": True, "use_gravity": False},
        {"$type": "teleport_object", "id": wall_id, "position": tele_pos}
    ]
    if wall_material is not None:
        commands.extend([
            tdw_object.get_add_material(wall_material, library="materials_high.json"),
            {"$type": "set_visual_material", "id": wall_id, "material_name": wall_material,
             "object_name": "PrimCube_0",
             "material_index": 0}
        ])
    if color is not None:
        commands.extend([
            {"$type": "set_color", "color": color, "id": wall_id},
        ])
    tdw_object.communicate(commands)
    return wall_id


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


class RampButton(Button.Button):
    def __init__(self, scale):
        self.scale = scale
        self.reset_param = 1
        Button.Button.__init__(self)

    def action(self, tdw_object):
        tdw_object.communicate({"$type": "scale_object", "id":  self.object_data["ramp"], "scale_factor":  {"x": 1, "y":self.scale, "z": 1}})
        self.reset_param = self.reset_param / self.scale


def get_platform():
    if sys.platform.startswith("linux"):
        return "Linux"
    elif sys.platform.startswith("darwin"):
        return "Darwin"
    else:
        return "Windows"


def get_offline_model_url(model_name, tdw_object):
    platform = get_platform()
    file_name = os.path.join(tdw_object.asset_path, "3d_models", platform, model_name)
    return "file:///" + file_name


def create_offline_model(tdw_object, position, rotation, model_name="prim_sphere"):
    model_id = tdw_object.get_unique_id()
    url = get_offline_model_url(model_name, tdw_object)
    tdw_object.communicate({"$type": "add_object",
                            "name": model_name,
                            "url": url,
                            "scale_factor": 1,
                            "id": model_id,
                            "position": position,
                            "rotation": rotation})
    return model_id


def create_offline_material(tdw_object, material_name):
    url = get_offline_model_url(material_name, tdw_object)
    tdw_object.communicate({"$type": "add_material", "name": material_name, "url": url})


def create_main_sphere_old(tdw_object, tele_pos):
    sphere = create_offline_model(tdw_object, position={"x": -4.825, "y": 3, "z": -5.012},
                                  rotation={"x": 0, "y": 0, "z": 0}, model_name="prim_sphere")
    # sphere = tdw_object.add_object("prim_sphere", position={"x": -4.825, "y": 3, "z": -5.012},
    #                                rotation = {"x": 0, "y": 0, "z": 0}, library = "models_special.json")

    scale = {"x": 0.1, "y": 0.1, "z": 0.1}
    commands = [
        {"$type": "set_color",
         "color": {"r": 214 / 255, "g": 52 / 255, "b": 71 / 255, "a": 1.0},
         "id": sphere},
        {"$type": "scale_object", "id": sphere, "scale_factor": scale},
        teleport_object_cmd(sphere, tele_pos),
        {"$type": "set_mass", "id": sphere, "mass": 7.0},
        {"$type": "set_physic_material", "id": sphere, "dynamic_friction": 0.1,
         "static_friction": 0.1,
         "bounciness": 0.6}
    ]
    tdw_object.communicate(commands)
    return sphere


def create_target_sphere_old(tdw_object, pos, tele_pos, high_value=False):
    sphere = create_offline_model(tdw_object, position=pos,
                                  rotation={"x": 0, "y": 0, "z": 0}, model_name="prim_sphere")
    # sphere = tdw_object.add_object("prim_sphere", position=pos, rotation = {"x": 0, "y": 0, "z": 0},
    #                                library="models_special.json")
    scale = {"x": 0.1, "y": 0.1, "z": 0.1}
    if not high_value:
        color = object_configs.touch_sphere["before_color"]
    else:
        color = object_configs.high_value_touch_sphere["before_color"]
    tdw_object.communicate([
        {"$type": "scale_object", "id": sphere, "scale_factor": scale},
        {"$type": "set_color",
         "color": color,
         "id": sphere},
        {"$type": "set_mass", "id": sphere, "mass": 10},
        {"$type": "set_physic_material", "dynamic_friction": 0.1,
         "static_friction": 0.1,
         "bounciness": 0.6, "id": sphere},
        teleport_object_cmd(sphere, tele_pos)
    ])
    return sphere


def create_sound_sphere_old(tdw_object, pos, tele_pos):
    amp = [0.1, 0.2, 0.3, 0.5, 0.6, 0.7]
    material = ["hardwood", "glass", "ceramic", "metal", "cardboard"]
    mass = [20, 10, 2, 100]
    bounciness = [0.6]

    sphere = {
        "mass": random.sample(mass, 1)[0],
        "amp": random.sample(amp, 1)[0],
        "bounciness": random.sample(bounciness, 1)[0],
        "material": random.sample(material, 1)[0]
    }

    sphere = tdw_object.add_object("prim_sphere", position=pos,
                                   rotation={"x": 0, "y": 0, "z": 0}, library="models_special.json")
    scale = {"x": 0.1, "y": 0.1, "z": 0.1}

    tdw_object.communicate([
        {"$type": "scale_object", "id": sphere, "scale_factor": scale},
        {"$type": "set_color",
         "color": object_configs.touch_sphere["before_color"],
         "id": sphere},
        {"$type": "set_mass", "id": sphere, "mass": 1},
        {"$type": "set_physic_material", "dynamic_friction": 0.1,
         "static_friction": 0.1,
         "bounciness": 0.9, "id": sphere},
        teleport_object_cmd(sphere, tele_pos)
    ])
    return sphere


def create_push_sphere(tdw_object, pos, tele_pos):
    sphere = tdw_object.add_object("prim_sphere", position=pos,
                                   rotation={"x": 0, "y": 0, "z": 0}, library="models_special.json")
    scale = {"x": 0.1, "y": 0.1, "z": 0.1}
    tdw_object.communicate({"$type": "scale_object", "id": sphere, "scale_factor": scale})
    # car_iridescent_paint
    tdw_object.communicate({"$type": "set_color",
     "color": object_configs.push_sphere["before_color"],
     "id": sphere}
        )
    tdw_object.communicate({"$type": "set_mass", "id": sphere, "mass": 1})
    teleport_object(tdw_object, sphere, tele_pos)
    return sphere


def create_cube_old(tdw_object, profile, pos, tele_pos):
    colors = [{"r": 15/255, "g": 76/255, "b": 126/255, "a": 1.0},
              {"r": 134 / 255, "g": 42 / 255, "b": 92 / 255, "a": 1.0},
              {"r": 244 / 255, "g": 244 / 255, "b": 77 / 255, "a": 1.0}
              ]
    # colors = [ {"r": 247 / 255, "g": 183 / 255, "b": 29 / 255, "a": 1.0},
    #             {"r": 247 / 255, "g": 183 / 255, "b": 29 / 255, "a": 1.0},
    #           {"r": 244 / 255, "g": 244 / 255, "b": 77 / 255, "a": 1.0}
    #           ]
    # colors = [{"r": 247 / 255, "g": 183 / 255, "b": 29 / 255, "a": 1.0},
    #           {"r": 247 / 255, "g": 183 / 255, "b": 29 / 255, "a": 1.0},
    #           {"r": 247 / 255, "g": 183 / 255, "b": 29 / 255, "a": 1.0}
    #           ]

    mass = [100, 5, 100]
    params = [
        {"$type": "set_physic_material",  "dynamic_friction": 0.1, "static_friction": 0.1, "bounciness": 0.6},
        {"$type": "set_physic_material",  "dynamic_friction": 0.1, "static_friction": 0.1, "bounciness": 0.6},
        {"$type": "set_physic_material",  "dynamic_friction": 0.2, "static_friction": 0.2, "bounciness": 0.6}
    ]


    cube_id = create_offline_model(tdw_object, position=pos, rotation={"x": 0, "y": 0, "z": 0}, model_name="prim_cube")
    # cube_id = tdw_object.add_object("prim_cube", position=pos, rotation={"x": 0, "y": 0, "z": 0},
    #                                 library="models_special.json")
    cube_params = params[profile]
    cube_params['id'] = cube_id
    tdw_object.communicate([
        {"$type": "set_mass", "id": cube_id, "mass": mass[profile]},
        {"$type": "scale_object", "id": cube_id, "scale_factor": {"x": 0.1, "y": 0.1, "z": 0.1}},
        {"$type": "set_color", "color": colors[profile], "id": cube_id},
        {"$type": "teleport_object", "id": cube_id, "position": tele_pos},
        cube_params
    ])

    return cube_id


def create_cube_breakable(tdw_object, pos, tele_pos, scale={"x":0.1, "y":0.1, "z":0.1}):
    cone_id = tdw_object.add_object("prim_cone", position=pos, rotation={"x": 0, "y": 0, "z": 0}, library="models_special.json")
    tdw_object.communicate([
        {"$type": "set_mass", "id": cone_id, "mass": 1},
        {"$type": "scale_object", "id": cone_id, "scale_factor": scale},
        {"$type": "set_color", "color": {"r": 255 / 255, "g": 115 / 255, "b": 21 / 255, "a": 1.0}, "id": cone_id},
        {"$type": "teleport_object", "id": cone_id, "position": tele_pos}
    ])
    tdw_object.communicate({"$type": "set_physic_material", "bounciness": 1.0, "dynamic_friction": 1.0, "id": cone_id, "static_friction": 1.0})

    return cone_id


def create_wall(tdw_object, x, z, mode, side, length, gap=0.141, profile=None):
    global global_object_creator, global_ptr, global_list
    reset_param = {}
    if (global_ptr + length) > len(global_list):
        global_ptr = 0
    if profile is None:
        profile = [random.randint(0,1) for _ in range(length)]
        global_ptr += length
    idx = 0
    if mode == "h":
        for _ in range(length):
            global_object_creator["x"] = global_object_creator["x"] - 1.1
            pos = dict({"x": x, "y": 0.8749, "z": z})
            cube_id = create_cube_old(tdw_object, profile[idx], dict(global_object_creator), pos)
            reset_param[cube_id] = pos
            if side == "r":
                x = x + gap
            else:
                x = x - gap
            idx += 1
    if mode == "v":
        for _ in range(length):
            global_object_creator["x"] = global_object_creator["x"] - 1.1
            pos = dict({"x": x, "y": 0.8749, "z": z})
            cube_id = create_cube_old(tdw_object, profile[idx], dict(global_object_creator), pos)
            reset_param[cube_id] = pos
            if side == "u":
                z = z + gap
            else:
                z = z - gap
            idx += 1
    return reset_param


def create_cyl(tdw_object, profile, tele_pos, rot={"x": 0, "y": 0, "z": 90}, scale={"x": 0.1, "y": 0.1, "z": 0.1}):
    global global_object_creator, global_ptr
    global_object_creator["x"] = global_object_creator["x"] - 1.1
    material_list = ["linen_viscose_classic_pattern", "plastic_vinyl_glossy_orange", "polyester_sport_fleece_brushed"]
    mass = [100, 10, 50]
    params = [{"$type": "set_physic_material", "dynamic_friction": 0.1,
               "static_friction": 0.1,
               "bounciness": 0.5},
              {"$type": "set_physic_material", "dynamic_friction": 0.3,
               "static_friction": 0.3,
               "bounciness": 0.1},
              {"$type": "set_physic_material", "dynamic_friction": 0.2,
               "static_friction": 0.2,
               "bounciness": 0.9}
              ]
    cyl = tdw_object.add_object("prim_cyl", position=dict(global_object_creator), rotation=rot, library="models_special.json")

    tdw_object.communicate([
        {"$type": "set_mass", "id": cyl, "mass": mass[profile]},
        {"$type": "scale_object", "id": cyl, "scale_factor": scale},
        {"$type": "set_visual_material", "id": cyl, "new_material_name": material_list[profile],
         "object_name": "PrimCyl_0",
         "old_material_index": 0},
        {"$type": "teleport_object", "id": cyl, "position": tele_pos}
    ])

    cube_params = params[profile]
    cube_params['id'] = cyl
    tdw_object.communicate(cube_params)
    return cyl


def lever(tdw_object, pos, orientation="h", centering=0, side="r"):
    # create_cyl(1, pos, scale={"x": 0.09, "y": 0.3, "z": 0.09})
    # stopper1 = create_cyl(1, {"x": -3.990618, "y": 0.886, "z": -4.208851}, {"x": 0, "y": 0, "z": 0},
    #                       scale={"x": 0.01, "y": 0.06, "z": 0.01})
    # stopper2 = create_cyl(1, {"x": -3.990618, "y": 0.886, "z": -4.307}, {"x": 0, "y": 0, "z": 0},
    #                       scale={"x": 0.01, "y": 0.06, "z": 0.01})
    # tdw.send_to_server({"$type": "set_kinematic_state", "id": stopper1, "is_kinematic": True, "use_gravity": False})
    # tdw.send_to_server({"$type": "set_kinematic_state", "id": stopper2, "is_kinematic": True, "use_gravity": False})
    reset_params = {}
    gap = 0.0522
    stopper1_pos = dict(pos)
    stopper2_pos = dict(pos)
    if orientation == "h":
        cyl_id = create_cyl(tdw_object, 1, pos, rot={"x": 0, "y": 0, "z": 90}, scale={"x": 0.09, "y": 0.3, "z": 0.09})
        reset_params[cyl_id] = {
            "position": dict(pos),
            "rotation": {"x": 0, "y": 0, "z": 90}
        }
        stopper1_pos["z"] = stopper1_pos["z"] - gap
        stopper2_pos["z"] = stopper2_pos["z"] + gap
        if side == "r":
            stopper1_pos["x"] = stopper1_pos["x"] + centering
            stopper2_pos["x"] = stopper2_pos["x"] + centering
        else:
            stopper1_pos["x"] = stopper1_pos["x"] - centering
            stopper2_pos["x"] = stopper2_pos["x"] - centering
        stopper1 = create_cyl(tdw_object, 1, stopper1_pos, {"x": 0, "y": 0, "z": 0},
                              scale={"x": 0.01, "y": 0.06, "z": 0.01})
        stopper2 = create_cyl(tdw_object, 1, stopper2_pos, {"x": 0, "y": 0, "z": 0},
                              scale={"x": 0.01, "y": 0.06, "z": 0.01})
    if orientation == "v":
        cyl_id = create_cyl(tdw_object, 1, pos, rot={"x": 90, "y": 0, "z": 0}, scale={"x": 0.09, "y": 0.2, "z": 0.09})
        reset_params[cyl_id] = {
            "position": dict(pos),
            "rotation": {"x": 90, "y": 0, "z": 0}
        }
        stopper1_pos["x"] = stopper1_pos["x"] - gap
        stopper2_pos["x"] = stopper2_pos["x"] + gap
        if side == "r":
            stopper1_pos["z"] = stopper1_pos["z"] + centering
            stopper2_pos["z"] = stopper2_pos["z"] + centering
        else:
            stopper1_pos["z"] = stopper1_pos["z"] - centering
            stopper2_pos["z"] = stopper2_pos["z"] - centering
        stopper1 = create_cyl(tdw_object, 1, stopper1_pos, {"x": 0, "y": 0, "z": 0},
                              scale={"x": 0.01, "y": 0.06, "z": 0.01})
        stopper2 = create_cyl(tdw_object, 1, stopper2_pos, {"x": 0, "y": 0, "z": 0},
                              scale={"x": 0.01, "y": 0.06, "z": 0.01})

    tdw_object.communicate({"$type": "set_kinematic_state", "id": stopper1, "is_kinematic": True, "use_gravity": False})
    tdw_object.communicate({"$type": "set_kinematic_state", "id": stopper2, "is_kinematic": True, "use_gravity": False})
    return reset_params


def lever_gate(tdw_object, pos, orientation="h", inside=1):
    reset_params = {}
    gap = 0.0522
    stopper1_pos = dict(pos)
    stopper2_pos = dict(pos)
    centering = 0.22
    if orientation == "h":
        cyl_id = create_cyl(tdw_object, 1, pos, rot={"x": 0, "y": 0, "z": 90}, scale={"x": 0.09, "y": 0.25, "z": 0.09})
        reset_params[cyl_id] = {
            "position": dict(pos),
            "rotation": {"x": 0, "y": 0, "z": 90}
        }
        stopper1_pos["z"] = stopper1_pos["z"] - gap*inside
        stopper2_pos["z"] = stopper2_pos["z"] - gap*inside

        stopper1_pos["x"] = stopper1_pos["x"] + centering
        stopper2_pos["x"] = stopper2_pos["x"] - centering

        stopper1 = create_cyl(tdw_object, 1, stopper1_pos, {"x": 0, "y": 0, "z": 0},
                              scale={"x": 0.01, "y": 0.06, "z": 0.01})
        stopper2 = create_cyl(tdw_object, 1, stopper2_pos, {"x": 0, "y": 0, "z": 0},
                              scale={"x": 0.01, "y": 0.06, "z": 0.01})
    if orientation == "v":
        cyl_id = create_cyl(tdw_object, 1, pos, rot={"x": 90, "y": 0, "z": 0}, scale={"x": 0.09, "y": 0.25, "z": 0.09})
        reset_params[cyl_id] = {
            "position": dict(pos),
            "rotation": {"x": 90, "y": 0, "z": 0}
        }
        stopper1_pos["x"] = stopper1_pos["x"] - gap*inside
        stopper2_pos["x"] = stopper2_pos["x"] - gap*inside

        stopper1_pos["z"] = stopper1_pos["z"] + centering
        stopper2_pos["z"] = stopper2_pos["z"] - centering
        stopper1 = create_cyl(tdw_object, 1, stopper1_pos, {"x": 0, "y": 0, "z": 0},
                              scale={"x": 0.01, "y": 0.06, "z": 0.01})
        stopper2 = create_cyl(tdw_object, 1, stopper2_pos, {"x": 0, "y": 0, "z": 0},
                              scale={"x": 0.01, "y": 0.06, "z": 0.01})

    tdw_object.communicate({"$type": "set_kinematic_state", "id": stopper1, "is_kinematic": True, "use_gravity": False})
    tdw_object.communicate({"$type": "set_kinematic_state", "id": stopper2, "is_kinematic": True, "use_gravity": False})
    return reset_params


def lever_small(tdw_object, pos, orientation="h", centering=0, side="r", lower_stopper=True, upper_stopper=True):
    gap = 0.0522
    stopper1_pos = dict(pos)
    stopper2_pos = dict(pos)
    reset_params = {}
    if orientation == "h":

        cyl_id = create_cyl(tdw_object, 1, pos, rot={"x": 0, "y": 0, "z": 90}, scale={"x": 0.09, "y": 0.2, "z": 0.09})
        reset_params[cyl_id] = {
            "position": dict(pos),
            "rotation": {"x": 0, "y": 0, "z": 90}
        }
        stopper1_pos["z"] = stopper1_pos["z"] - gap
        stopper2_pos["z"] = stopper2_pos["z"] + gap
        if side == "r":
            stopper1_pos["x"] = stopper1_pos["x"] + centering
            stopper2_pos["x"] = stopper2_pos["x"] + centering
        else:
            stopper1_pos["x"] = stopper1_pos["x"] - centering
            stopper2_pos["x"] = stopper2_pos["x"] - centering
        if lower_stopper:
            stopper1 = create_cyl(tdw_object, 1, stopper1_pos, {"x": 0, "y": 0, "z": 0},
                                  scale={"x": 0.01, "y": 0.06, "z": 0.01})
        if upper_stopper:
            stopper2 = create_cyl(tdw_object, 1, stopper2_pos, {"x": 0, "y": 0, "z": 0},
                                  scale={"x": 0.01, "y": 0.06, "z": 0.01})
    if orientation == "v":
        cyl_id = create_cyl(tdw_object, 1, pos, rot={"x": 90, "y": 0, "z": 0}, scale={"x": 0.09, "y": 0.2, "z": 0.09})
        reset_params[cyl_id] = {
            "position": dict(pos),
            "rotation": {"x": 90, "y": 0, "z": 0}
        }
        stopper1_pos["x"] = stopper1_pos["x"] - gap
        stopper2_pos["x"] = stopper2_pos["x"] + gap
        if side == "r":
            stopper1_pos["z"] = stopper1_pos["z"] + centering
            stopper2_pos["z"] = stopper2_pos["z"] + centering
        else:
            stopper1_pos["z"] = stopper1_pos["z"] - centering
            stopper2_pos["z"] = stopper2_pos["z"] - centering
        if lower_stopper:
            stopper1 = create_cyl(tdw_object, 1, stopper1_pos, {"x": 0, "y": 0, "z": 0},
                                  scale={"x": 0.01, "y": 0.06, "z": 0.01})
        if upper_stopper:
            stopper2 = create_cyl(tdw_object, 1, stopper2_pos, {"x": 0, "y": 0, "z": 0},
                                  scale={"x": 0.01, "y": 0.06, "z": 0.01})
    if lower_stopper:
        tdw_object.communicate({"$type": "set_kinematic_state", "id": stopper1, "is_kinematic": True, "use_gravity": False})
    if upper_stopper:
        tdw_object.communicate({"$type": "set_kinematic_state", "id": stopper2, "is_kinematic": True, "use_gravity": False})
    return reset_params


def create_goal(tdw_object, x, z):
    gap = 0.11
    create_wall(tdw_object, x, z, "v", "d", 3, gap=gap, profile=[2]*3)
    create_wall(tdw_object, x + gap, z - 3*gap, "h", "r", 3, gap=gap,profile=[2] * 3)
    create_wall(tdw_object, x + 4*gap, z, "v", "d", 3, gap=gap, profile=[2] * 3)
    boundaries = {
        "z_top": z,
        "z_bottom": z - 0.2281,
        "x_left": x + 0.1012,
        "x_right": x + 0.3381
    }
    return boundaries


def create_breakable_wall(tdw_object, x, z, mode, side, length, gap=0.141, y=0.8749):
    reset_params = {}
    global global_object_creator, global_ptr, global_list
    idx = 0
    if mode == "h":
        for _ in range(length):
            global_object_creator["x"] = global_object_creator["x"] - 1.1
            pos = dict({"x": x, "y": 0.8332242, "z": z})
            wall_id = create_cube_breakable(tdw_object, dict(global_object_creator), pos, scale={"x": 0.1, "y": 0.1, "z": 0.1})

            reset_params[wall_id] = pos
            if side == "r":
                x = x + gap
            else:
                x = x - gap
            idx += 1
    if mode == "v":
        for _ in range(length):
            global_object_creator["x"] = global_object_creator["x"] - 1.1
            pos = dict({"x": x, "y": 0.8332242, "z": z})
            wall_id = create_cube_breakable(tdw_object, dict(global_object_creator), pos, scale={"x": 0.1, "y": 0.1, "z": 0.1})
            reset_params[wall_id] = pos
            if side == "u":
                z = z + gap
            else:
                z = z - gap
            idx += 1
    return reset_params


def create_cube_stack(tdw_object, stack_length, x, z, profiles=None):
    y = 0.8830635
    reset_params = {}
    global global_object_creator, global_ptr, global_list
    idx = 0
    for _ in range(stack_length):
        global_object_creator["x"] = global_object_creator["x"] - 1.1
        new_pos = dict(global_object_creator)
        new_pos["y"] = 0
        if profiles != None and len(profiles) == stack_length:
            pos = {"x": x, "y": y, "z": z}
            cube_id = create_cube_old(tdw_object, profiles[idx], dict(global_object_creator), pos)
            reset_params[cube_id] = pos
            idx += 1
        y = y + 0.09991
    step_one_frame(tdw_object, 100)
    return reset_params


def create_rectangle(tdw_object, pos, rot):
    global global_object_creator
    mass = [10, 5, 100]
    params = [{"$type": "set_physic_material", "dynamic_friction": 0.1,
               "static_friction": 0.1,
               "bounciness": 0.5},
              {"$type": "set_physic_material", "dynamic_friction": 0.1,
               "static_friction": 0.1,
               "bounciness": 0.1},
              {"$type": "set_physic_material", "dynamic_friction": 0.2,
               "static_friction": 0.2,
               "bounciness": 0.9}
              ]
    global_object_creator["x"] = global_object_creator["x"] - 1.1
    _pos = dict({"x": global_object_creator["x"], "y": 0.8332242, "z": global_object_creator["z"]})
    cube = tdw_object.add_object("prim_cube", position=_pos, rotation=rot, library="models_special.json")

    tdw_object.communicate([
        {"$type": "set_mass", "id": cube, "mass": mass[1]},
        {"$type": "scale_object", "id": cube, "scale_factor": {"x": 0.1, "y": 0.1, "z": 0.3}},
        {"$type": "set_color", "color": object_configs.rectangle["before_color"],
         "id": cube},
        {"$type": "teleport_object", "id": cube, "position": pos}
    ])

    cube_params = params[1]
    cube_params['id'] = cube
    tdw_object.communicate(cube_params)
    reset_params = {
        cube: {
            "position": dict(pos),
            "rotation": dict(rot)
        }
    }
    return reset_params


def create_inventory_items(tdw_object):
    inventory_list_ids = []
    max_cube_numbers = 20
    max_wall_piece_number = 7
    max_adversarial_patches_numbers = 16
    print("Creating Inventory Items ...")
    object_inventory = {
        "cube": {
            "not_used": {},
            "used": {}
        },
        "touch_sphere": {
            "not_used": {},
            "used": {}
        },
        "high_value_touch_sphere": {
            "not_used": {},
            "used": {}
        },
        "wall_pieces": {
            "not_used": {},
            "used": {}
        },
        "ramp":{
            "not_used": {},
            "used": {}
        },
        "ad_patch":{
            "not_used": {},
            "used": {}
        },
    }
    cube_profiles = [0, 1]
    obj_positions = {"x": 3.39, "y": 0, "z": -10.3}
    # Create main sphere
    sphere_id = create_main_sphere_old(tdw_object, obj_positions)
    inventory_list_ids.append(sphere_id)
    object_inventory["main_sphere"] = (sphere_id, obj_positions.copy())
    obj_positions["z"] += 0.3
    # Create Cubes
    for profile in cube_profiles:
        gen_objs = []
        obj_positions["x"] = 4
        for _ in range(max_cube_numbers):
            cube_id = create_cube_old(tdw_object, profile=profile, pos={"x": 3, "y": 4, "z": 2}, tele_pos=obj_positions)
            gen_objs.append((cube_id, obj_positions.copy()))
            inventory_list_ids.append(cube_id)
            obj_positions["x"] += 0.3
        obj_positions["z"] += 0.3
        object_inventory["cube"]["not_used"][profile] = gen_objs
        object_inventory["cube"]["used"][profile] = []
    # Create touch spheres
    gen_objs = []
    obj_positions["x"] = 4
    for _ in range(max_cube_numbers):
        target_sphere_id = create_target_sphere_old(tdw_object, pos={"x": 3, "y": 4, "z": 2}, tele_pos=obj_positions)
        gen_objs.append((target_sphere_id, obj_positions.copy()))
        inventory_list_ids.append(target_sphere_id)
        obj_positions["x"] += 0.3
    obj_positions["z"] += 0.3
    object_inventory["touch_sphere"]["not_used"][0] = gen_objs
    object_inventory["touch_sphere"]["used"][0] = []

    # High value target
    gen_objs2 = []
    obj_positions["x"] = 4
    for _ in range(max_cube_numbers):
        target_sphere_id = create_target_sphere_old(tdw_object, pos={"x": 3, "y": 4, "z": 2}, tele_pos=obj_positions, high_value=True)
        gen_objs2.append((target_sphere_id, obj_positions.copy()))
        inventory_list_ids.append(target_sphere_id)
        obj_positions["x"] += 0.3
    obj_positions["z"] += 0.3
    object_inventory["high_value_touch_sphere"]["not_used"][0] = gen_objs2
    object_inventory["high_value_touch_sphere"]["used"][0] = []

    # create wall pieces
    wall_orientations = ["h", "v", "c1", "c2", "c3", "c4", "vb", "vt", "hr", "hl"]
    for wall_orientation in wall_orientations:
        obj_positions["x"] = 4
        wall_pieces = []
        for _ in range(max_wall_piece_number):
            scale, rotation = get_wall_scale_orientation(wall_orientation)
            wall_id = create_wall_piece_inventory(tdw_object, scale, pos={"x": 3, "y": 4, "z": 2},
                                                  tele_pos=obj_positions, rotation=rotation)
            wall_pieces.append((wall_id, obj_positions.copy()))
            obj_positions["x"] += 0.3
        obj_positions["z"] += 0.3
        object_inventory["wall_pieces"]["not_used"][wall_orientation] = wall_pieces
        object_inventory["wall_pieces"]["used"][wall_orientation] = []

    # create ramps
    obj_positions["x"] = 4
    obj_positions["z"] += 0.7
    ramp_id = create_ramp_inventory(tdw_object, obj_positions)
    object_inventory["ramp"]["not_used"][0] = [(ramp_id, obj_positions.copy())]
    object_inventory["ramp"]["used"][0] = []

    # create paintings
    obj_positions["x"] = 4
    obj_positions["z"] += 0.7
    ad_patches = []

    for _ in range(max_adversarial_patches_numbers):
        painting_ids = create_adversarial_area_inventory(tdw_object, obj_positions)

        ad_patches.append((painting_ids, obj_positions.copy()))
        obj_positions["x"] += 0.3

    object_inventory["ad_patch"]["not_used"][0] = ad_patches
    object_inventory["ad_patch"]["used"][0] = []

    objs = [ e[0] for e in object_inventory["cube"]["not_used"][0]] +\
    [e[0] for e in object_inventory["cube"]["not_used"][1]] +\
    [e[0] for e in object_inventory["touch_sphere"]["not_used"][0]] + [object_inventory["main_sphere"][0]] + \
    [e[0] for e in object_inventory["high_value_touch_sphere"]["not_used"][0]]

    objs_ = []
    for wall_profiles in object_inventory["wall_pieces"]["not_used"].keys():
        objs_.extend([e[0] for e in object_inventory["wall_pieces"]["not_used"][wall_profiles]])
    objs_ = objs + objs_

    commands = [
        {"$type": "send_collisions", "enter": True, "exit": True, "stay": True},
                {"$type": "send_transforms", "frequency": "always", "ids": objs},
                {"$type": "send_rigidbodies", "frequency": "always", "ids": objs},
                ]
    commands.extend([{"$type": "set_object_collision_detection_mode", "id": e, "mode": "continuous_speculative"} for e in objs_])
    tdw_object.communicate(commands)
    return object_inventory, inventory_list_ids


def create_adversarial_area_inventory(tdw_object, painting_position):
    file_name = pkg_resources.resource_filename(__name__, 'data/orange.jpg')
    with open(file_name, "rb") as f:
        image = b64encode(f.read()).decode("utf-8")
    painting_id = tdw_object.get_unique_id()
    dimensions = {"x": 1, "y": 1}
    painting_position = {"x": painting_position["x"], "y": 1, "z": painting_position["z"]}
    tdw_object.communicate([{"$type": "create_painting",
                             "position": painting_position,
                             "size": {"x": 0.141, "y": 0.141},
                             "euler_angles": {"x": 90, "y": 0, "z": 0},
                             "id": painting_id},
                            {"$type": "set_painting_texture",
                             "id": painting_id,
                             "dimensions": dimensions,
                             "image": image}
                            ])

    return painting_id


def create_adversarial_area(tdw_object, x, z, is_center=False, object_inventory={}):

    selected_ad_patches_tuple = object_inventory["ad_patch"]["not_used"][0].pop(0)
    painting_id = selected_ad_patches_tuple[0]
    object_inventory["ad_patch"]["used"][0].append(selected_ad_patches_tuple)
    painting_position = {"x": x, "y": 0.8324, "z": z}
    tdw_object.communicate([
        {"$type": "teleport_painting", "position": painting_position, "id": painting_id}
    ])
    highlighted_areas = {
        painting_id: ""
    }
    if is_center:
        diff = 0.1601
        boundaries = {
            "z_top": z + diff,
            "z_bottom": z - diff,
            "x_left": x - diff,
            "x_right": x + diff
        }
        return highlighted_areas, boundaries
    return highlighted_areas, None


def create_ramp_inventory(tdw_object, pos, rot={"x": 0, "y": 90, "z": 0}, scale={"x": 0.1, "y": 0.11, "z": 0.1}):
    global global_object_creator, global_ptr
    global_object_creator["x"] = global_object_creator["x"] - 1.1
    # Create ramp increase decrease buttons
    if rot["y"] == 270:
        pos["x"] += 0.096
    elif rot["y"] == 90:
        pos["x"] -= 0.096
    ramp = tdw_object.add_object("ramp_with_platform", position=dict(global_object_creator), rotation=rot, library="models_special.json")

    tdw_object.communicate([
        {"$type": "scale_object", "id": ramp, "scale_factor": scale},
        {"$type": "teleport_object", "id": ramp, "position": pos},
        {"$type": "set_kinematic_state", "id": ramp, "is_kinematic": True, "use_gravity": False},
        {"$type": "set_color",
         "color": {"r": 98 / 255, "g": 55 / 255, "b": 78 / 255, "a": 1.0},
         "id": ramp},
    ])
    # If the ramp is changeable than create two button
    return ramp


def get_wall_scale_orientation(wall_orientation):
    wall_length = 0.141
    thickness = 0.024
    if wall_orientation == "h":
        return {"x": wall_length, "y": 0.1, "z": thickness}, {"x": 0, "y": 0, "z": 0}
    elif wall_orientation == "v":
        return {"x": thickness, "y": 0.1, "z": wall_length}, {"x": 0, "y": 0, "z": 0}
    elif wall_orientation == "c1":
        return {"x": 0.105, "y": 0.1, "z": thickness},  {"x": 0, "y": -45, "z": 0}
    elif wall_orientation == "c2":
        return {"x": 0.105, "y": 0.1, "z": thickness}, {"x": 0, "y": 45, "z": 0}
    elif wall_orientation == "c3":
        return {"x": 0.105, "y": 0.1, "z": thickness},  {"x": 0, "y": 45, "z": 0}
    elif wall_orientation == "c4":
        return {"x": 0.105, "y": 0.1, "z": thickness}, {"x": 0, "y": -45, "z": 0}
    elif wall_orientation == "vb":
        return {"x": thickness, "y": 0.1, "z": wall_length/2}, {"x": 0, "y": 0, "z": 0}
    elif wall_orientation == "vt":
        return {"x": thickness, "y": 0.1, "z": wall_length/2}, {"x": 0, "y": 0, "z": 0}
    elif wall_orientation == "hr":
        return {"x": wall_length/2, "y": 0.1, "z": thickness}, {"x": 0, "y": 0, "z": 0}
    elif wall_orientation == "hl":
        return {"x": wall_length/2, "y": 0.1, "z": thickness}, {"x": 0, "y": 0, "z": 0}


def create_wall_piece_inventory(tdw_object, wall_scale, pos, tele_pos, rotation):
    wall_id = tdw_object.add_object("prim_cube", position=pos, rotation=rotation, library="models_special.json")
    tdw_object.communicate([
        {"$type": "scale_object", "id": wall_id, "scale_factor": wall_scale},
        {"$type": "set_kinematic_state", "id": wall_id, "is_kinematic": True, "use_gravity": False},
        {"$type": "teleport_object", "id": wall_id, "position": tele_pos}
    ])
    return wall_id


def create_cube_new(tdw_object, object_inventory, cube_pos, profile):
    available_cubes = object_inventory["cube"]["not_used"][profile]
    selected_cube_tuple = available_cubes[random.randint(0, len(available_cubes) - 1)]
    cmd = teleport_object_cmd(selected_cube_tuple[0], cube_pos)

    object_inventory["cube"]["not_used"][profile].remove(selected_cube_tuple)
    object_inventory["cube"]["used"][profile].append(selected_cube_tuple)
    if profile == 0:
        selected_profile = 2
    else:
        selected_profile = 3
    return {selected_cube_tuple[0]: cube_pos}, object_inventory, cmd, selected_profile


def create_target_sphere_new(tdw_object, object_inventory, sphere_pos):
    available_spheres = object_inventory["touch_sphere"]["not_used"][0]
    if len(available_spheres) > 0:
        idx = random.randint(0, len(available_spheres) - 1)
    else:
        idx = 0
    selected_sphere_tuple = available_spheres[idx]

    cmd = teleport_object_cmd(selected_sphere_tuple[0], sphere_pos)
    object_inventory["touch_sphere"]["not_used"][0].remove(selected_sphere_tuple)
    object_inventory["touch_sphere"]["used"][0].append(selected_sphere_tuple)
    return {selected_sphere_tuple[0]: sphere_pos}, object_inventory, cmd


def create_high_value_target_sphere_new(tdw_object, object_inventory, sphere_pos):
    available_spheres = object_inventory["high_value_touch_sphere"]["not_used"][0]
    if len(available_spheres) > 0:
        idx = random.randint(0, len(available_spheres) - 1)
    else:
        idx = 0
    selected_sphere_tuple = available_spheres[idx]

    cmd = teleport_object_cmd(selected_sphere_tuple[0], sphere_pos)
    object_inventory["high_value_touch_sphere"]["not_used"][0].remove(selected_sphere_tuple)
    object_inventory["high_value_touch_sphere"]["used"][0].append(selected_sphere_tuple)
    return {selected_sphere_tuple[0]: sphere_pos}, object_inventory, cmd


def create_main_sphere_new(tdw_object, object_inventory, sphere_pos):
    sphere_id = object_inventory["main_sphere"][0]
    teleport_object(tdw_object, sphere_id, sphere_pos)
    cmd = teleport_object_cmd(sphere_id, sphere_pos)
    return {sphere_id: sphere_pos}, cmd


def create_cube_stack_new(tdw_object, object_inventory, stack_length, x, z, profiles=None):
    y = 0.8830635
    reset_params = {}
    global global_object_creator, global_ptr, global_list
    idx = 0
    cmds = []
    for _ in range(stack_length):
        global_object_creator["x"] = global_object_creator["x"] - 1.1
        new_pos = dict(global_object_creator)
        new_pos["y"] = 0
        if profiles != None and len(profiles) == stack_length:
            pos = {"x": x, "y": y, "z": z}
            profile = random.choice([0, 1])
            cube_param, object_inventory, cmd, _ = create_cube_new(tdw_object, object_inventory, pos, profile)
            cmds.append(cmd)
            reset_params.update(cube_param)
            idx += 1
        y = y + 0.09991
    tdw_object.communicate(cmds)
    # step_one_frame(tdw_object, 100)
    return reset_params, object_inventory
