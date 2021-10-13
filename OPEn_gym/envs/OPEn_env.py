import gym
from OPEn_gym.envs.utils import gym_utils, object_configuration, primitives
from tdw.output_data import Images, OutputData, Collision, Transforms, Rigidbodies
from PIL import Image as pil_Image
import io
import numpy as np
from gym import spaces
from tdw.py_impact import PyImpact
from OPEn_gym.envs.utils.proc_gen import create_puzzle


class OPEnEnv(gym.Env):
    metadata = {'render.modes': ['human', "rgb_array"]}

    def __init__(self, tdw_ip, self_ip, asset_path, port=None, debug=True, audio_dir=None):
        print("Creating new Environment")
        print(port)
        self.tdw_ip = tdw_ip
        self.port = port
        if tdw_ip is None or tdw_ip == "none" or tdw_ip == "None":
            launch_build = True
        else:
            self.tdw_docker_id = gym_utils.setup_tdw_instance(tdw_ip, self_ip, port, audio_dir)
            launch_build = False
        print(f"Connecting with tdw on port {self.port}")
        self.tdw_instance = gym_utils.TDW_sim(1, self.port, asset_path, launch_build)
        self.puzzle_type = "non-goal"
        # self.tdw_instance.run(debug=debug)
        self.tdw_instance.run(proc_gen=True, debug=debug)
        scene_object_ids = gym_utils.load_initial_objects(self.tdw_instance)
        self.output_images = False
        self.reward_tracker = {}
        self.puzzle_loaded = False
        self.episode = False
        self.object_affected = []
        self.reward_off = False
        self.action_space = spaces.Discrete(9)
        self.observation_space = spaces.Box(0, 255, [self.tdw_instance.option["height"], self.tdw_instance.option["width"], 3], dtype=np.uint8)
        self.agent_obs = "dict"
        self.last_action_state = {
            "steps": 0
        }
        self.reward_informer = 0
        self.previous_agent_distance = None
        self.current_frame = np.zeros([self.tdw_instance.option["height"], self.tdw_instance.option["width"], 3])
        self.set_output_image = False
        self.puzzle_number = None
        self._elapsed_steps = 0
        self.skip_frame = False
        self.adversarial_collision = False
        self.task = None
        self.special_case = False
        # self.p = PyImpact(initial_amp=0.01)
        self._max_episode_steps = None
        self.object_inventory, self.inventory_ids = primitives.create_inventory_items(self.tdw_instance)
        self.inventory_ids.extend(scene_object_ids)
        print("Tdw initialised")
        # self.p = PyImpact(initial_amp=0.01)

    def configure_env(self, skip_frame=True):
        """
        Configure the gym to send image/object dictionary. Make the red ball physics based or not
        """
        self.skip_frame = skip_frame

    def step(self, action):
        """
            Parameters
            ----------
            action :

            Returns
            -------
            ob, reward, episode_over, info : tuple
                ob (object) :
                    an environment-specific object representing your observation of
                    the environment.
                reward (float) :
                    amount of reward achieved by the previous action. The scale
                    varies between environments, but the goal is always to increase
                    your total reward.
                episode_over (bool) :
                    whether it's time to reset the environment again. Most (but not
                    all) tasks are divided up into well-defined episodes, and done
                    being True indicates the episode has terminated. (For example,
                    perhaps the pole tipped too far, or you lost your last life.)
                info (dict) :
                     diagnostic information useful for debugging. It can sometimes
                     be useful for learning (for example, it might contain the raw
                     probabilities behind the environment's last state change).
                     However, official evaluations of your agent are not allowed to
                     use this for learning.
        """
        resp, self.last_action_state = self.tdw_instance.take_action(action, self.last_action_state, self.skip_frame)
        obs = {}
        obs['object_information'] = {}
        # print(self._max_episode_steps)
        # Initialize current step re
        self.reward_informer = 0
        self.adversarial_collision = False
        objects_that_matter = list(self.tdw_instance.objects["model_names"].keys())
        collision_in_scene = False
        collided_objects = []
        update_image = None
        for r in resp:
            r_id = OutputData.get_data_type_id(r)
            if r_id == "imag":
                images = Images(r)
                obs['image'] = np.array(pil_Image.open(io.BytesIO(images.get_image(0)))).astype(np.uint8)
            if r_id == "coll":
                collision_data = Collision(r)
                update_image_ = self.process_collision(collision_data)
                if collision_data.get_collider_id() not in collided_objects and self.tdw_instance.objects["sphere"] != \
                        collision_data.get_collider_id():
                    collided_objects.append(collision_data.get_collider_id())
                if collision_data.get_collidee_id() not in collided_objects and self.tdw_instance.objects["sphere"] != \
                        collision_data.get_collidee_id():
                    collided_objects.append(collision_data.get_collider_id())
                if update_image is None:
                    update_image = update_image_
            if r_id == "rigi":
                rigi_body_data = Rigidbodies(r)
                for object_index in range(rigi_body_data.get_num()):
                    if rigi_body_data.get_id(object_index) not in obs['object_information'].keys() and \
                            rigi_body_data.get_id(object_index) in objects_that_matter:
                        obs['object_information'][rigi_body_data.get_id(object_index)] = {}
                    if rigi_body_data.get_id(object_index) in obs['object_information'].keys():
                        obs['object_information'][rigi_body_data.get_id(object_index)][
                            'velocity'] = rigi_body_data.get_velocity(object_index)
                        obs['object_information'][rigi_body_data.get_id(object_index)][
                            'mass'] = rigi_body_data.get_mass(object_index)
                        obs['object_information'][rigi_body_data.get_id(object_index)][
                            'angular_velocity'] = rigi_body_data.get_angular_velocity(object_index)
            if r_id == "tran":
                transform_data = Transforms(r)
                for object_index in range(transform_data.get_num()):
                    if transform_data.get_id(object_index) not in obs['object_information'].keys() and \
                            transform_data.get_id(object_index) in objects_that_matter:
                        obs['object_information'][transform_data.get_id(object_index)] = {}
                    if transform_data.get_id(object_index) in obs['object_information'].keys():
                        obs['object_information'][transform_data.get_id(object_index)][
                            'position'] = transform_data.get_position(object_index)
                        obs['object_information'][transform_data.get_id(object_index)][
                            'rotation'] = transform_data.get_rotation(object_index)
        # Play the sound
        wav_data = []
        # wav_data = self.play_audio(resp)

        if update_image is not None:
            obs["image"] = update_image
        for objs in objects_that_matter:
            if objs in collided_objects:
                collision_in_scene = True
                break
        for key in obs["object_information"].keys():
            obs["object_information"][key]["model_name"] = self.tdw_instance.objects["model_names"][key]
        update_img = self.get_reward(obs['object_information'])
        if update_img is not None and "image" in obs:
            obs["image"] = update_img

        if self.adversarial_collision and not self.reward_off:
            self.reward_informer += -1
            self.episode = True
        self.process_buttons(obs["object_information"])
        self.get_color_information(obs)
        if not self.reward_off:
            self.update_episode_state(obs['object_information'])
        if "image" in obs:
            self.current_frame = obs["image"]
        self._elapsed_steps += 1
        if self.reward_off:
            self.reward_informer = 0
            self.episode = False
        # obs['object_information']["collision"] = collision_in_scene
        # obs['object_information']["wav_data"] = wav_data
        return obs, self.reward_informer, self.episode, obs['object_information']

    def play_audio(self, resp):
        collisions, environment_collision, rigidbodies = PyImpact.get_collisions(resp)

        objects = self.tdw_instance.objects
        main_sphere = objects["sphere"]
        impact_sound_command = []

        profiles = {
            1: {
                "material": "glass",
                "amp": 0.3,
                "mass": 10,
                "bounciness": 0.6,
                "model": "sphere"
            },
            2: {
                "material": "wood",
                "amp": 0.01,
                "mass": 100,
                "bounciness": 0.6,
                "model": "cube"
            },
            3: {
                "material": "ceramic",
                "amp": 0.3,
                "mass": 5,
                "bounciness": 0.6,
                "model": "cube"
            },
            4: {
                "material": "metal",
                "amp": 0.3,
                "mass": 7,
                "bounciness": 0.6,
                "model": "agent_sphere"
            },
            5: {
                "material": "cardboard",
                "amp": 0.3,
                "mass": 2,
                "bounciness": 0.6,
                "model": "agent_sphere"
            }
        }
        # Go through every collision and check if the object involved are in union of sound listener and main sphere
        sound_listener_id = [e[0] for e in objects["sound_listener"]]
        sound_listener_profile = [e[1] for e in objects["sound_listener"]]
        wav_data = []
        for col in collisions:
            collision_data = col
            if (collision_data.get_collidee_id() == main_sphere or collision_data.get_collider_id() == main_sphere) \
                    and \
                    (collision_data.get_collidee_id() in sound_listener_id or collision_data.get_collider_id() in sound_listener_id):
                tgt_id = collision_data.get_collidee_id() if collision_data.get_collidee_id() != main_sphere\
                    else collision_data.get_collider_id()
                cmd = self.p.get_impact_sound_command(
                    collision=col,
                    rigidbodies=rigidbodies,
                    target_id=tgt_id,
                    target_mat=profiles[sound_listener_profile[sound_listener_id.index(tgt_id)]]["material"],
                    target_amp=profiles[sound_listener_profile[sound_listener_id.index(tgt_id)]]["amp"],
                    other_id=main_sphere,
                    other_amp=profiles[4]["amp"],
                    other_mat=profiles[4]["material"])
                impact_sound_command.append(cmd)
                # print(profiles[sound_listener_profile[sound_listener_id.index(tgt_id)]]["material"], tgt_id, cmd)
        if impact_sound_command:
            self.tdw_instance.communicate(impact_sound_command)
            wav_data.extend([e["wav_data"] for e in impact_sound_command])
        return wav_data

    def process_buttons(self, object_information):
        if object_information:
            for button in self.tdw_instance.objects["buttons"]:
                if button.is_button_pressed(object_information):
                    button.action(self.tdw_instance)

    def turn_off_reward(self, value):
        """
        Used for exporting environment with intrinsic reward
        """
        self.reward_off = value

    def get_color_information(self, obs):
        object_configs = object_configuration.object_configuration()
        for key in obs["object_information"].keys():
            # if main sphere
            if key == self.tdw_instance.objects["sphere"]:
                obs["object_information"][key]["color_id"] = object_configs.main_sphere["color_id"]
            # If it's a push sphere
            elif key in self.tdw_instance.objects["push_spheres"]:
                if self.reward_tracker[key] != 0:
                    obs["object_information"][key]["color_id"] = object_configs.push_sphere["after_color_id"]
                else:
                    obs["object_information"][key]["color_id"] = object_configs.push_sphere["before_color_id"]
            # if it's touc sphere
            elif key in self.tdw_instance.objects['target_spheres']:
                if self.reward_tracker[key] != 0:
                    obs["object_information"][key]["color_id"] = object_configs.touch_sphere["after_color_id"]
                else:
                    obs["object_information"][key]["color_id"] = object_configs.touch_sphere["before_color_id"]
            elif key in self.tdw_instance.objects['high_value_target']:
                if self.reward_tracker[key] != 0:
                    obs["object_information"][key]["color_id"] = object_configs.high_value_touch_sphere["after_color_id"]
                else:
                    obs["object_information"][key]["color_id"] = object_configs.high_value_touch_sphere["before_color_id"]
            # If it's a cube
            elif obs["object_information"][key]["model_name"] == "prim_cube":
                if obs["object_information"][key]["mass"] == object_configs.cube_1["mass"]:
                    obs["object_information"][key]["color_id"] = object_configs.cube_1["color_id"]
                elif obs["object_information"][key]["mass"] == object_configs.cube_2["mass"]:
                    obs["object_information"][key]["color_id"] = object_configs.cube_2["color_id"]
            else:
                print(f"{key} not found")

    def check_highlight(self, object_information):
        # Test: Check if the physical material changes fast enough
        x = -3.776
        z = -5.472
        diff = 0.304
        for tgt_sphere in self.tdw_instance.objects['target_spheres'] + [self.tdw_instance.objects['sphere']] + self.tdw_instance.objects["push_spheres"]:
            pos = object_information[tgt_sphere]["position"]
            if (x - diff) < pos[0] < (x + diff) and (z - diff) < pos[2] < (z + diff) and tgt_sphere not in self.object_affected:
                print("Object in highlighted area.... changing physical params")
                self.object_affected.append(tgt_sphere)
                self.tdw_instance.communicate({"$type": "set_physic_material", "id": tgt_sphere, "dynamic_friction": 1,
                                               "static_friction": 1, "bounciness": 0.5})

    def process_collision(self, collision_data):
        objects = self.tdw_instance.objects
        img = None
        if "walls" in objects.keys():
            wall_ids = objects["walls"]
            # Check for adversarial cones
            if (collision_data.get_collider_id() in wall_ids or collision_data.get_collidee_id() in wall_ids) and (objects["sphere"] == collision_data.get_collider_id() or objects["sphere"] == collision_data.get_collidee_id()):
                if not self.reward_off:
                    self.adversarial_collision = True
                    return
        # Check for main sphere and touch ball collision
        if (objects["sphere"] == collision_data.get_collider_id() and collision_data.get_collidee_id() in objects[
            "target_spheres"]) or (
                objects["sphere"] == collision_data.get_collidee_id() and collision_data.get_collider_id() in
                objects["target_spheres"]):

            img = self.update_reward(
                collision_data.get_collidee_id() if collision_data.get_collidee_id() in objects[
                    "target_spheres"] else collision_data.get_collider_id())

        # Check for main sphere and touch ball collision
        if (objects["sphere"] == collision_data.get_collider_id() and collision_data.get_collidee_id() in objects[
            "high_value_target"]) or (
                objects["sphere"] == collision_data.get_collidee_id() and collision_data.get_collider_id() in
                objects["high_value_target"]):
            img = self.update_reward(
                collision_data.get_collidee_id() if collision_data.get_collidee_id() in objects[
                    "high_value_target"] else collision_data.get_collider_id())

        return img

    def update_episode_state(self, object_information=None):
        # Makesure all balls are on the table else end the episode
        if object_information is not None and object_information:
            for _sphere in self.tdw_instance.objects['target_spheres'] + [self.tdw_instance.objects['sphere']] + \
                           self.tdw_instance.objects['push_spheres']:
                try:
                    pos = object_information[_sphere]["position"]
                    if not (-0.706 < pos[0] < 0.706 and -1.187 < pos[2] < 1.187):
                        self.episode = True
                        return
                except:
                    print("{} not present in ")

        # If episode is already done than return
        if self.episode:
            return
        # Check reward tracker
        for key, value in self.reward_tracker.items():
            if value != 1:
                self.episode = False
                return
        # If all targets are achieved and reward is not turned_off, end episode
        if not self.reward_off:
            self.episode = True

    def update_reward(self, tgt_id):
        img = None
        object_configs = object_configuration.object_configuration()
        if self.reward_tracker[tgt_id] == 0:
            # Mark as target achieved
            self.reward_tracker[tgt_id] = 1
            if tgt_id in self.tdw_instance.objects["high_value_target"]:
                self.reward_informer = 1
                if not self.reward_off:
                    img = self.tdw_instance.change_material(tgt_id, object_configs.high_value_touch_sphere["after_color"])
            elif tgt_id in self.tdw_instance.objects["target_spheres"]:
                if self.task == 2:
                    self.reward_informer = 0.1
                else:
                    self.reward_informer = 1
                if not self.reward_off:
                    img = self.tdw_instance.change_material(tgt_id, object_configs.touch_sphere["after_color"])
        return img

    def add_change_puzzle(self, task=None, puzzle_config=None, puzzle_data=None, max_episode_steps=None):
        if puzzle_data is None:
            puzzle_data = create_puzzle(task, puzzle_config=puzzle_config)

        if task == 0 or puzzle_config is not None:
            self.turn_off_reward(True)
        else:
            self.turn_off_reward(False)
        if max_episode_steps is None:
            self._max_episode_steps = self.get_timesteps(task)
        else:
            self._max_episode_steps = max_episode_steps

        self.task = task
        if self.puzzle_loaded:
            if self.puzzle_loaded:
                dragged_obj, commands = gym_utils.clear_scene(self.tdw_instance.objects, self.object_inventory)
                self.tdw_instance.communicate(dragged_obj)
                self.tdw_instance.communicate(commands)
        self.tdw_instance.objects, self.puzzle_type, self.object_inventory = gym_utils.load_puzzle_proc_gen(self.tdw_instance, puzzle_data, self.object_inventory, self.inventory_ids)
        self.init_reward(self.tdw_instance.objects)
        self.puzzle_loaded = True
        self.episode = False
        self.reset(just_the_variables=True)

    def get_timesteps(self, task):
        timesteps = {
            "task_0": None,
            "task_1": 30,
            "task_2": 30,
            "task_3": 50,
            "task_4": 180
        }
        return timesteps["task_{}".format(task)]

    def get_reward(self, object_information=None):
        object_configs = object_configuration.object_configuration()
        img = None
        # If there is adversarial area
        if "adversarial_boundary" in self.tdw_instance.objects:
            adversarial_boundary = self.tdw_instance.objects["adversarial_boundary"]
            pos = object_information[self.tdw_instance.objects["sphere"]]["position"]
            if adversarial_boundary["x_left"] < pos[0] < adversarial_boundary["x_right"] and \
                    adversarial_boundary["z_bottom"] < pos[2] < adversarial_boundary["z_top"]:
                self.adversarial_collision = True
        # Special case code
        if 'goal_boundaries' in self.tdw_instance.objects and self.task == 4:
            # Check if main sphere is inside

            pos = object_information[self.tdw_instance.objects["sphere"]]["position"]
            goal_boundaries = self.tdw_instance.objects["goal_boundaries"]
            if not(goal_boundaries["x_left"] < pos[0] < goal_boundaries["x_right"]
                    and goal_boundaries["z_bottom"] < pos[2] < goal_boundaries["z_top"]):
                if self.special_case is False:
                    self.reward_informer += 1
                    self.special_case = True
        if self.puzzle_type == 'goal' or self.puzzle_type == "hybrid":
            if 'goal_boundaries' in self.tdw_instance.objects:
                for tgt_sphere in self.tdw_instance.objects['push_spheres']:
                    pos = object_information[tgt_sphere]["position"]
                    goal_boundaries = self.tdw_instance.objects["goal_boundaries"]
                    if goal_boundaries["x_left"] < pos[0] < goal_boundaries["x_right"] and goal_boundaries["z_bottom"] < \
                            pos[2] < goal_boundaries["z_top"]:
                        if self.reward_tracker[tgt_sphere] != 1:
                            self.reward_tracker[tgt_sphere] = 1
                            img = self.tdw_instance.change_material(tgt_sphere, object_configs.push_sphere["after_color"])
                            self.reward_informer += 1
                    # If the ball has reward but it is out of goal turn it back
                    elif self.reward_tracker[tgt_sphere] == 1:
                        img = self.tdw_instance.change_material(tgt_sphere, object_configs.push_sphere["before_color"])
                        self.reward_tracker[tgt_sphere] = 0
                        self.reward_informer -= 1
                        self.init_reward(self.tdw_instance.objects)
                        self.episode = False
        return img

    def set_observation(self, output=False):
        self.set_output_image = output
        self.tdw_instance.output_images(output)

    def init_reward(self, objects):
        self.reward_tracker = {}
        self.reward_informer = 0
        for sphere in objects["target_spheres"] + objects["push_spheres"] + objects["high_value_target"]:
            self.reward_tracker[sphere] = 0

    def reset(self, just_the_variables=False):
        if not just_the_variables:
            gym_utils.reset_scene(self.tdw_instance, self.tdw_instance.objects)
        self.init_reward(self.tdw_instance.objects)
        self.episode = False
        self._elapsed_steps = 0
        self.special_case = False
        # self.p.reset()
        o, _, done, _ = self.step(0)
        return o

    def render(self, mode='human'):
        if mode == "rgb_array":
            return self.current_frame
        else:
            return None

    def _get_reward(self):
        """ Reward is given for XY. """
        pass

    def _seed(self):
        pass

    def get_maximum_reward(self):
        return len(self.reward_tracker.keys())

    def close(self):
        if self.tdw_ip is not None:
            gym_utils.kill_tdw(self.tdw_ip, self.tdw_docker_id)
        else:
            self.tdw_instance.communicate({"$type": "terminate"})
        self.tdw_instance = None