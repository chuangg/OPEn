from os.path import isdir, join
import random
from os import mkdir, getcwd
from json import loads
import os
import json


exp_no = 0
directory = join(getcwd(), "dist")
if not isdir(directory):
    mkdir(directory)
obj_list = []
ready = False
image_count1 = 0
image_count2 = 0
objects = []
avatar = []
avatar_ball_collision = False
objects_ready = False
object_data = None
task = None


def step_one_frame(tdw_object, n):
    for i in range(n):
        tdw_object.communicate({"$type": "do_nothing"})


def teleport_object_cmd(obj_id, pos):
    return {"$type": "teleport_object", "id": obj_id, "position": pos}


def teleport_object(tdw_object, obj_id, pos):
    tdw_object.communicate({"$type": "teleport_object", "id": obj_id, "position": pos})






