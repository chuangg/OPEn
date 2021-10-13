
import random
import gym
import json
import time
from PIL import Image
import imageio
import numpy as np
if __name__ == '__main__':
    env = gym.make('OPEn_gym:OPEn_env-v0', tdw_ip=None, self_ip="localhost", port=None, debug=False)
    puzzle_config = {
        "main_sphere": 1,
        # "ramp": 1,
        "main_sphere_i_j": [(8, 4)],
        "touch_sphere": 2,
        "cube": 3,
        "high_value_target": 2,
        # "adversarial_patch": 1,
        # "stack": 1
    }
    task = 1
    # data = np.load(f"record/puzzle_data_{task}.npy")
    env.add_change_puzzle(task, puzzle_config=puzzle_config)
    # 1,1 -> Goal seeking Task
    # 1,2 -> Preference Task
    # 1,3 -> Avoidance Task
    # 1, 1.5 -> Tool use
    env.set_observation(True)
    env.configure_env(skip_frame=False)
    frames = []
    duration = 100
    while duration > 0:
    # for i in range(200):
        # start = time.time()
        # time.sleep(2)
        # env.add_change_puzzle(1, 2, puzzle_config)
        # env.reset()
        # print(time.time() - start)
        # if i %2 == 0:
        obs, rewards, dones, info = env.step(env.action_space.sample())
        duration -= 1
        frames.append(obs["image"])
        # img = obs["image"]
        # img = Image.fromarray(img)
        # img.save(f"data/img-{i}.png")
        # env.add_change_puzzle(0, diff, puzzle_config)
    #     sound_list = obs["object_information"]["wav_data"]
    #     final_sound.append({
    #         i: sound_list
    #     })
    # with open("out.pickle", "wb") as fp:
    #     pickle.dump(final_sound, fp, protocol=pickle.HIGHEST_PROTOCOL)
        # if rewards != 0:
        #     print(rewards)
        # else:
        #     obs, rewards, dones, info = env.step(0)

        # obs, rewards, dones, info = env.step(random.sample([2, 4, 6, 8], 1)[0])
        # for k in obs["object_information"].keys():
        #     if "color_id" in obs["object_information"][k]:
        #         if obs["object_information"][k]["color_id"] == 3:
        #             print(json.dumps(obs["object_information"][k]["velocity"], indent=2))
        # if i %100 ==0:
        # if dones:
        #     env.add_change_puzzle(1, 5.1, puzzle_config)
        # if i == 0:
        #     obs, rewards, dones, info = env.step(1)
        # else:
        #     obs, rewards, dones, info = env.step(0)

            # for k in obs["object_information"].keys():
            #     if obs["object_information"][k]["color_id"] == 3:
            #         print(json.dumps(obs["object_information"][k], indent=2))

    imageio.mimsave("out.gif", frames)

# 0.6239471435546875
# # 0.6005749702453613
# # 0.5706138610839844
# # 0.628497838973999
# # 0.5231328010559082
# # 0.6151916980743408
# # 0.5528769493103027
# # 0.5297350883483887
# # 0.5988900661468506
# # 1.1057541370391846
# # 0.5907919406890869
# # 0.7549760341644287
# # 0.6657767295837402
# # 0.5509250164031982
# # 0.5589821338653564
# # 0.538114070892334
# # 0.6118142604827881
# # 0.589346170425415
# # 0.5573141574859619
# # 0.5411748886108398
# # 0.5973911285400391
# # 0.7942399978637695
# # 0.6336212158203125