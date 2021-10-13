import pygame
import gym
import numpy as np
import os
import pickle
import shutil
from PIL import Image

def eval_reward(reward, task):
    if task == 1:
        return reward
    if task == 2:
        if reward == 1:
            return 0.8
        elif reward == 0.1:
            return 0.2
        elif reward == 1.1:
            return 1.0
        else:
            return 0
    if task == 3:
        if reward == 1:
            return reward
        else:
            return 0
    if task == 4:
        if reward == 2:
            return 1
        else:
            return 0

pygame.init()

env = gym.make('gym_tdw:tdw_puzzle_proc-v0', tdw_ip='localhost', port=None, self_ip=None, debug=False)
task = 0
difficulty = 1
puzzle_config = {

    "main_sphere": 1,
    # "ramp": 1,
    # "main_sphere_i_j": [(8, 4)],
    # "touch_sphere": 3,
    "cube": 5,
    "high_value_target": 0,
    # "adversarial_patch": 1,
    "stack": 1
}
puzzle_data = np.load(f"puzzles/task{difficulty}/puzzle_no_0.npy")
env.add_change_puzzle(task, difficulty, puzzle_data=puzzle_data)
# env.add_change_puzzle(task, difficulty, puzzle_config=puzzle_config)
env.set_observation(True)
pressed_left = pressed_right = pressed_up = pressed_down = power_up = stop = False
force_mag = 1
_task = None
_difficulty_0 = None
_difficulty_1 = None
_difficulty = None
scene_image = None
episode_done = False
puzzle_done = False
env.configure_env(False, action_space="full")
step = 0
total_reward = 0
puzzle_number = 1
puzzle_rewards = []
puzzle_steps = []
puzzle_results = {}
per_step = []
per_step_rew = []
total_per_step_rew = []
max_ouzzles = 100
idx = 0
# env.turn_off_reward(True)
if os.path.isdir(f"task_{difficulty}_img"):
    shutil.rmtree(f"task_{difficulty}_img")
os.mkdir(f"task_{difficulty}_img")
while True:
    action = 0
    episode_done = False
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:  # check for key presses
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:  # left arrow turns left
                pressed_left = True
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:  # right arrow turns right
                pressed_right = True
            elif event.key == pygame.K_UP or event.key == pygame.K_w:  # up arrow goes up
                pressed_up = True
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:  # down arrow goes down
                pressed_down = True
            elif event.key == pygame.K_z or event.key == pygame.K_m:
                power_up = True
            elif event.key == pygame.K_r:
                env.reset()
            elif event.key == pygame.K_c:
                # env.add_change_puzzle(task, difficulty, puzzle_config=puzzle_config)
                if puzzle_number < 100:
                    puzzle_data = np.load(f"puzzles/task{difficulty}/puzzle_no_{puzzle_number}.npy")
                    env.add_change_puzzle(task, difficulty, puzzle_data=puzzle_data)
                    puzzle_number += 1
                    puzzle_done = False
                else:
                    print("Reached the end")
            elif event.key == pygame.K_x or event.key == pygame.K_n:
                stop = True
            elif event.key == pygame.K_u:
                print("Saving scene")
                # save_puzzle(puzzle_data, task, difficulty)
                # save_image(scene_image, task, difficulty)
            elif event.key == pygame.K_1:
                if _task is None:
                    _task = 1
                elif _difficulty_0 is None:
                    _difficulty_0 = 1
                elif _difficulty_1 is None:
                    _difficulty_1 = 1
            elif event.key == pygame.K_2:
                if _task is None:
                    _task = 2
                elif _difficulty_0 is None:
                    _difficulty_0 = 2
                elif _difficulty_1 is None:
                    _difficulty_1 = 2
            elif event.key == pygame.K_3:
                if _task is None:
                    _task = 3
                elif _difficulty_0 is None:
                    _difficulty_0 = 3
                elif _difficulty_1 is None:
                    _difficulty_1 = 3
            elif event.key == pygame.K_4:
                if _task is None:
                    _task = 4
                elif _difficulty_0 is None:
                    _difficulty_0 = 4
                elif _difficulty_1 is None:
                    _difficulty_1 = 4
            elif event.key == pygame.K_5:
                if _task is None:
                    _task = 5
                elif _difficulty_0 is None:
                    _difficulty_0 = 5
                elif _difficulty_1 is None:
                    _difficulty_1 = 5
            elif event.key == pygame.K_6:
                if _task is None:
                    _task = 6
                elif _difficulty_0 is None:
                    _difficulty_0 = 6
                elif _difficulty_1 is None:
                    _difficulty_1 = 6
            elif event.key == pygame.K_7:
                if _task is None:
                    _task = 7
                elif _difficulty_0 is None:
                    _difficulty_0 = 7
                elif _difficulty_1 is None:
                    _difficulty_1 = 7
            elif event.key == pygame.K_8:
                if _task is None:
                    _task = 8
                elif _difficulty_0 is None:
                    _difficulty_0 = 8
                elif _difficulty_1 is None:
                    _difficulty_1 = 8
            elif event.key == pygame.K_9:
                if _task is None:
                    _task = 9
                elif _difficulty_0 is None:
                    _difficulty_0 = 9
                elif _difficulty_1 is None:
                    _difficulty_1 = 9
            elif event.key == pygame.K_0:
                if _task is None:
                    _task = 0
                elif _difficulty_0 is None:
                    _difficulty_0 = 0
                elif _difficulty_1 is None:
                    _difficulty_1 = 0

        elif event.type == pygame.KEYUP:  # check for key releases
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:  # left arrow turns left
                pressed_left = False
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:  # right arrow turns right
                pressed_right = False
            elif event.key == pygame.K_UP or event.key == pygame.K_w:  # up arrow goes up
                pressed_up = False
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:  # down arrow goes down
                pressed_down = False
            elif event.key == pygame.K_z or event.key == pygame.K_m:
                power_up = False
            elif event.key == pygame.K_x or event.key == pygame.K_n:
                stop = False
    if _task is not None and _difficulty_0 is not None and _difficulty_1 is not None:
        _difficulty = _difficulty_0 * 10 + _difficulty_1
        if 1 <= _task <= 1:
            if _task == 1:
                if not 1 <= _difficulty <= 4:
                    _task, _difficulty_0, _difficulty_1, _difficulty = None, None, None, None
        else:
            _task, _difficulty_0, _difficulty_1, _difficulty = None, None, None, None
        if _difficulty == 4:
            _difficulty = 5.1
    if _task and _difficulty:
        task = _task
        difficulty = _difficulty
        puzzle_data = np.load(f"puzzles/task{difficulty}/puzzle_no_0.npy")
        env.add_change_puzzle(task, difficulty, puzzle_data=puzzle_data)
        puzzle_number = 1
        total_per_step_rew = []
        puzzle_steps = []
        puzzle_rewards = []
        obs = env.reset()
        scene_image = obs["image"]
        _task = None
        _difficulty_0 = None
        _difficulty_1 = None
        _difficulty = None
    if stop:
        action = 9
    elif pressed_right and pressed_up:
        action = 2
    elif pressed_up and pressed_left:
        action = 4
    elif pressed_left and pressed_down:
        action = 6
    elif pressed_down and pressed_right:
        action = 8
    if pressed_left:
        action = 5
    if pressed_right:
        action = 1
    if pressed_up:
        action = 3
    if pressed_down:
        action = 7
    obs, reward, episode_done, _ = env.step(action)
    if action != 0:
        img = Image.fromarray(obs["image"])
        img.save(f"task_{difficulty}_img/img_{idx}.png")
        idx += 1
        step += 1
        total_reward += reward
        if difficulty == 2:
            per_step.append(step)
            per_step_rew.append(eval_reward(reward, difficulty))
    if episode_done:
        diff = difficulty if difficulty != 5.1 else 4
        puzzle_rewards.append(eval_reward(total_reward, diff))
        puzzle_steps.append(step)
        print(f"Task {diff} Puzzle number: {puzzle_number} Total reward: {eval_reward(total_reward, diff)} Total steps: {step}")
        # env.reset()

        step = 0
        total_reward = 0
        if difficulty == 2:
            total_per_step_rew.append(per_step_rew)
            per_step_rew = []

        puzzle_results[f"task{difficulty}"] = puzzle_steps
        if difficulty == 2:
            puzzle_results[f"task{difficulty}_rew"] = total_per_step_rew
        else:
            puzzle_results[f"task{difficulty}_rew"] = puzzle_rewards
        with open("result.pickle", "wb") as fp:
            pickle.dump(puzzle_results, fp, protocol=pickle.HIGHEST_PROTOCOL)

        if puzzle_number < max_ouzzles:
            puzzle_data = np.load(f"puzzles/task{diff}/puzzle_no_{puzzle_number}.npy")
            env.add_change_puzzle(task, difficulty, puzzle_data=puzzle_data)
            # env.add_change_puzzle(task, difficulty, puzzle_config=puzzle_config)
            puzzle_number += 10
            puzzle_done = False
        else:
            difficulty += 1
            if difficulty > 4:
                exit()
            diff = difficulty
            difficulty = 5.1 if difficulty == 4 else difficulty
            # puzzle_data = np.load(f"puzzles/task{diff}/puzzle_no_{0}.npy")
            env.add_change_puzzle(task, difficulty, puzzle_data=puzzle_data)
            env.add_change_puzzle(task, difficulty, puzzle_config=puzzle_config)
            puzzle_number = 1
            puzzle_done = False
            total_per_step_rew = []
            puzzle_steps = []
            puzzle_rewards = []





