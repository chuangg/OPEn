## Installing the environment

`git clone https://github.ibm.com/Abhi-B/gym-tdw.git`

`cd gym-tdw`

Download [3d_models](https://agent-dataset-storage.s3.us-east.cloud-object-storage.appdomain.cloud/3d_models.zip) and unzip

`pip install -e .`

## Running TDW on remote headless linux machine
It is possible to run TDW on a remote server with multiple GPU and no physical display attached to it. You can follow 
below steps to setup headless X server to run TDW and run the TDW service to run multiple TDW instances
* Follow these [steps](https://github.com/chuangg/tdw-transport-challenge-starter-code#setting-up-headless-x-server) to 
setup headless X server and these [steps](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker) 
to install nvidia-docker.
* Edit `rest_api.py` line number 9 to include list of all display servers you created in last steps. TDW instances will
  be evenly divided among these servers
* Start tmux session and run `python rest_api.py`. This will start a flask service that will create TDW docker 
  containers. This service is will divide multiple TDW containers evenly on multiple GPUs.
* To use this service simply set `tdw_ip` to `localhost` or the `<ip-address>` of the machine which is running rest_api.py 
  while creating the environment. Now you can create multiple envs and use the gym with SubprocVec

## Running the environment
The environment consist of a table with walled borders. 
The scene objects consist of:
* `Agent:` Red sphere that can move in 8 direction
* `Target Ball:` Yellow sphere that agent can either interact with or hit to get reward in downstream tasks
* `High value Target Ball:` Green sphere that agent can interact or hit to get reward (the reward is much higher than 
  yellow ball)
* `Purple cube:` A lightweight cube that agent can interact with or move out of way by hitting it
* `Blue cube:` Heavier cube that agent can interact or move out of way (or find a way around)
Scene object are randomly added to the table. The maximum number of each object depends on type of task or mode. The 
  exact number of objects, and their position is randomly generated and hence forms a unique configuration each time the
  environment is reset.
The environment has two modes:
### Open-ended exploration 
In this mode the agent can interact with scene objects. Because the environment is meant for open-ended 
exploration, the reward will always be zero and the episode will not end (done will always be false). In
this mode the agent can move in 8 directions and can collide with any object.
Example of using environment in this mode:
```python
import gym
import imageio

def main():
    # Tdw_ip can be localhost if running on same machine else the ip address of the machine
    env = gym.make('OPEn_gym:OPEn_env-v0', asset_path="<path to downloaded 3d_models>", tdw_ip=None, self_ip="localhost", port=None, debug=False)
    # You have to specify config that scene objects, maximum number for them, agent position (Will be placed randomly 
    # if not included) 
    # If no puzzle config is provided, random objects are selected and placed
    puzzle_config = {
        "main_sphere": 1,
        "main_sphere_i_j": [(8, 4)],
        "touch_sphere": 2,
        "cube": 3,
        "high_value_target": 2,
    }
    # Task 0 for open-ended exploration
    env.add_change_puzzle(task=0, puzzle_config=puzzle_config)
    # set this to get image in output observation
    env.set_observation(True)
    # If skip frame is true, environment will return output after 4 steps
    # If skip frame is false, environment will step 1 frame and will ignore all but every 4th action
    env.configure_env(skip_frame=False)
    duration  = 100
    frames = []
    while duration > 0:
      duration -= 1
      # apply random action
      obs, rewards, done, info = env.step(env.action_space.sample)
      frames.append(obs["image"])
    imageio.mimsave("output.gif", frames)
```
### Downstream Tasks
The environment includes 4 downstream task that each have different reward functions.
* `Task 1 - Goal-seeking:` In this task the agent has to hit goal object which is the yellow sphere. This task will 
  generate and position random number of blue and purple cubes which as obstacle. The agent has to learn efficient 
  policy for hitting the goal object. 
* `Task 2 - Preference:` In this task agent is placed at equiv-distant from two goal objects, a yellow and a green sphere.
  The distance between agent and goal object is randomly selected  everytime the environment is reset and in some cases,
  given limited number of steps (max steps allowed per episode is 30) the agent can only hit one goal object. 
  Hitting green sphere will give a much higher reward then yellow sphere and agent is expected to learn preference. 
  The obstacles in this task are also generated and placed randomly and include the blue and purple cubes 
* `Task 3 - Avoidance:` In this task agent has to hit the goal object, yellow sphere while avoiding the orange highlighted
  adversarial area. Going through this region will award negative reward, and the episode will end. The environment will 
  give reward for hitting the goal object. Just like before obstacles are randomly generated and placed.
* `Task 4 - Tool-use:` In this task the agent spawns inside a small bounded area surrounded by wall. The task involves 
  hitting the yellow ball for reward which is always spawned outside the walled region. The walled region also has a 
  ramp, and the agent is expected to learn to use this ramp to escape this region and hit the goal object. The 
  environment will give reward for escaping the region and  hitting goal object.
  
Here is an example of creating enviroment with downstream task:
```python
import gym
import imageio

def main():
    # Tdw_ip can be localhost if running on same machine else the ip address of the machine
    env = gym.make('OPEn_gym:OPEn_env-v0', asset_path="<path to downloaded 3d_models>", tdw_ip=None, self_ip="localhost", port=None, debug=False)
    # 1 for goal seeking task
    # 2 for preference task
    # 3 for avoidance task
    # 4 for tool use task
    env.add_change_puzzle(task=1)
    # set this to get image in output observation
    env.set_observation(True)
    # If skip frame is true environment will return output after 4 steps
    # If skip frame is false environment will step 1 frame and will ignore all but every 4th action
    env.configure_env(skip_frame=False)
    duration  = 100
    frames = []
    while duration > 0:
      duration -= 1
      # apply random action
      obs, rewards, done, info = env.step(env.action_space.sample)
      frames.append(obs["image"])
      if done:
        env.reset()
    imageio.mimsave("output.gif", frames)
      
```
