import carla
from carla import ColorConverter as cc
import random
import time
import cv2
import numpy as np
import math
import pygame
from ruamel.yaml import YAML
from pathlib import Path

from pygame.locals import K_a
from pygame.locals import K_w
from pygame.locals import K_d
from pygame.locals import K_x
from pygame.locals import K_f
from pygame.locals import K_t
from pygame.locals import K_h
from pygame.locals import K_b
from shared_memory_dict import SharedMemoryDict
smd = SharedMemoryDict(name='tokens', size=10000000)

# Read Config File
configfile=Path("config.yaml")
_config = YAML(typ='safe').load(configfile)

control_device=_config['sim']['default_control']

class mirror_parameters:
    def __init__(self):
        self.left_yaw=-150
        self.left_pitch=0
        self.right_yaw=150
        self.right_pitch=0


# Render object to keep and pass the PyGame surface
class RenderObject(object):
    def __init__(self, width, height):
        init_image = np.random.randint(0,255,(height,width,3),dtype='uint8')
        self.surface = pygame.surfarray.make_surface(init_image.swapaxes(0,1))

# Camera sensor callback, reshapes raw data from camera into 2D RGB and applies to PyGame surface
def pygame_callback(data, obj):
    img = np.reshape(np.copy(data.raw_data), (data.height, data.width, 4))
    img = img[:,:,:3]
    img = img[:, :, ::-1]

    obj.surface = pygame.surfarray.make_surface(img.swapaxes(0,1))

# Camera sensor callback, reshapes raw data from camera into 2D RGB and applies to PyGame surface
def process_image_data(image_data, view_id, flip=False):
    img = np.reshape(np.copy(image_data.raw_data), (image_data.height, image_data.width, 4))
    img = img[:,:,:3]
    img = img[:, :, ::-1]
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)	
    if flip:
        img=cv2.flip(img, 1)
    smd[view_id] = img

class controller ():
    def __init__(self, vehicle):
        self._control = carla.VehicleControl()
        self._steer_cache = 0.0

        try:

            # initialize steering wheel
            pygame.joystick.init()

            joystick_count = pygame.joystick.get_count()
            if joystick_count > 1:
                raise ValueError("Please Connect one Joystick")
            if joystick_count ==0 :
                raise ValueError("No joystick connected")

            self._joystick = pygame.joystick.Joystick(0)
            self._joystick.init()

            self._steer_idx = _config['sim']['controls'][control_device]['steering_wheel']
            self._throttle_idx = _config['sim']['controls'][control_device]['throttle']
            self._brake_idx = _config['sim']['controls'][control_device]['brake']
            self._reverse_idx = _config['sim']['controls'][control_device]['reverse']
            self._handbrake_idx = _config['sim']['controls'][control_device]['handbrake']
            self.vehicle=vehicle
        except Exception as e: 
            print(e)
            print('Shutting Down')
            client.apply_batch([carla.command.DestroyActor(x) for x in vehicle_list])
            world.apply_settings(original_settings)
            pygame.quit()
            print ("Done")
            exit (0)


    def parse_vehicle_wheel(self):
        numAxes = self._joystick.get_numaxes()
        jsInputs = [float(self._joystick.get_axis(i)) for i in range(numAxes)]
        # print (jsInputs)
        jsButtons = [float(self._joystick.get_button(i)) for i in
                        range(self._joystick.get_numbuttons())]

        # Custom function to map range of inputs [1, -1] to outputs [0, 1] i.e 1 from inputs means nothing is pressed
        # For the steering, it seems fine as it is
        K1 = 1.0  # 0.55
        steerCmd = K1 * math.tan(1.1 * jsInputs[self._steer_idx])
        if (steerCmd>-0.1 and steerCmd<=0.1):
            steerCmd=0

        K2 = 1.6  # 1.6
        throttleCmd = K2 + (2.05 * math.log10(
            -0.7 * jsInputs[self._throttle_idx] + 1.4) - 1.2) / 0.92
        if throttleCmd <= 0:
            throttleCmd = 0
        elif throttleCmd > 1:
            throttleCmd = 1
        throttleCmd=(abs(1-throttleCmd))

        brakeCmd = 1.6 + (2.05 * math.log10(
            -0.7 * jsInputs[self._brake_idx] + 1.4) - 1.2) / 0.92
        if brakeCmd <= 0:
            brakeCmd = 0
        elif brakeCmd > 1:
            brakeCmd = 1
        brakeCmd=(abs(1-brakeCmd))

        self._control.steer = steerCmd
        self._control.brake = brakeCmd
        self._control.throttle = throttleCmd

        #print (self._control.throttle)

        #toggle = jsButtons[self._reverse_idx]

        self._control.hand_brake = bool(jsButtons[self._handbrake_idx])

        self.vehicle.apply_control(self._control)
 
host='127.0.0.1'
port=2000
vehicle_list=[]
front_window_size=_config['sim']['windows']['front_res']
mirror_window_size=_config['sim']['windows']['mirror_res']
autopilot=False

mp=mirror_parameters()

# Connect to the client 
client = carla.Client(host, port)
client.set_timeout(200.0)

#world = client.load_world('Town04')
world = client.load_world('Town10HD_Opt')

'''
# Large World Loading
world = client.load_world('Town11')
settings = world.get_settings()
settings.tile_stream_distance = 2000
world.apply_settings(settings)
'''



# Load layered map for Town 01 with minimum layout plus buildings and parked vehicles
#world = client.load_world('Town10_Opt', carla.MapLayer.Buildings | carla.MapLayer.ParkedVehicles)
# Toggle all buildings off
#world.unload_map_layer(carla.MapLayer.Buildings)


# Getting the world and
world = client.get_world()
original_settings = world.get_settings()

# weather
weather = world.get_weather()
weather.sun_azimuth_angle = 344
weather.sun_altitude_angle = 45
weather.precipitation = 0
weather.precipitation_deposits = 0 # puddles
world.set_weather(weather)

# Set up the simulator in synchronous mode
settings = world.get_settings()
settings.synchronous_mode = True # Enables synchronous mode
settings.fixed_delta_seconds = 0.05
world.apply_settings(settings)

# Set up the TM in synchronous mode
traffic_manager = client.get_trafficmanager()
traffic_manager.set_synchronous_mode(True)

# Set a seed so behaviour can be repeated if necessary
traffic_manager.set_random_device_seed(0)
random.seed(0)

'''
# Print list of available vehicles
vehicle_blueprints = world.get_blueprint_library().filter('vehicle')
for car_bp in vehicle_blueprints:
    print (car_bp)
'''

vehicle_tag='charger_2020'

# Instanciating te vehicle to which we attached the sensors
bp = world.get_blueprint_library().filter(vehicle_tag)[0]
bp.set_attribute('role_name', 'hero' )
vehicle = world.spawn_actor(bp, random.choice(world.get_map().get_spawn_points()))
vehicle_list.append(vehicle)
vehicle.set_autopilot(autopilot)

# Find the blueprint of the sensor.
mirror_blueprint = world.get_blueprint_library().find('sensor.camera.rgb')
# Modify the attributes of the blueprint to set image resolution and field of view.
mirror_blueprint.set_attribute('image_size_x', str(mirror_window_size[0]))
mirror_blueprint.set_attribute('image_size_y', str(mirror_window_size[0]))
mirror_blueprint.set_attribute('fov', '110')


# Find the blueprint of the sensor.
car_blueprint = world.get_blueprint_library().find('sensor.camera.rgb')
# Modify the attributes of the blueprint to set image resolution and field of view.
car_blueprint.set_attribute('image_size_x', str(front_window_size[0]))
car_blueprint.set_attribute('image_size_y', str(front_window_size[1]))
car_blueprint.set_attribute('fov', '110')



# Set the time in seconds between sensor captures
###blueprint.set_attribute('sensor_tick', '1')

# Provide the position of the sensor relative to the vehicle.
#left_mirror_transform = carla.Transform(carla.Location(x=.7, y=-1, z=1.2), carla.Rotation(yaw=-150))
#right_mirror_transform = carla.Transform(carla.Location(x=.7, y=1, z=1.2), carla.Rotation(yaw=150))

left_mirror_transform = carla.Transform(carla.Location(x=.7, y=-1, z=1.2), carla.Rotation(pitch=mp.left_pitch, yaw=mp.left_yaw))
right_mirror_transform = carla.Transform(carla.Location(x=.7, y=1, z=1.2), carla.Rotation(pitch=mp.right_pitch,yaw=mp.right_yaw))

front_view_transform = carla.Transform(carla.Location(x=0.8, z=1.7))


# Tell the world to spawn the sensor, don't forget to attach it to your vehicle actor.
lmv_sensor = world.spawn_actor(mirror_blueprint, left_mirror_transform, attach_to=vehicle_list[0])
rmv_sensor = world.spawn_actor(mirror_blueprint, right_mirror_transform, attach_to=vehicle_list[0])
fv_sensor = world.spawn_actor(car_blueprint, front_view_transform, attach_to=vehicle_list[0])

# Subscribe to the sensor stream by providing a callback function, this function is
# called each time a new image is generated by the sensor.
fv_sensor.listen(lambda data: pygame_callback(data, renderObject))
rmv_sensor.listen(lambda data: process_image_data(data, "right_mirror_view", True))
lmv_sensor.listen(lambda data: process_image_data(data, "left_mirror_view", True))

# Game loop
crashed = False

# Get camera dimensions
image_w = car_blueprint.get_attribute("image_size_x").as_int()
image_h = car_blueprint.get_attribute("image_size_y").as_int()
renderObject = RenderObject(image_w, image_h)

pygame.init()
display = pygame.display.set_mode(front_window_size,  pygame.HWSURFACE | pygame.DOUBLEBUF, display=0 , vsync=1)  # pygame.FULLSCREEN |
# Draw black to the display
display.fill((0,0,0))
display.blit(renderObject.surface, (0,0))
pygame.display.flip()


my_controller=controller(vehicle)


while not crashed:
    # Advance the simulation time
    world.tick()

    my_controller.parse_vehicle_wheel()
    my_controller._control.reverse = my_controller._control.gear < 0
    
    # Update the display
    display.blit(renderObject.surface, (0,0))
    pygame.display.flip()

    for event in pygame.event.get():
        # If the window is closed, break the while loop
        if event.type == pygame.QUIT:
            crashed = True
        if event.type == pygame.JOYBUTTONDOWN:
                if event.button == my_controller._reverse_idx:
                    my_controller._control.gear = 1 if my_controller._control.reverse else -1
                    print ("Reverse", my_controller._control.gear )

        # Process Mirror Adjustments
        if event.type == pygame.KEYDOWN:
            if event.key == K_a:
                    mp.left_yaw += 1
            elif event.key == K_d:
                    mp.left_yaw += -1
            elif event.key == K_w:
                    mp.left_pitch += 1
            elif event.key == K_x:
                    mp.left_pitch += -1

            elif event.key == K_f:
                    mp.right_yaw += 1
            elif event.key == K_h:
                    mp.right_yaw += -1
            elif event.key == K_t:
                    mp.right_pitch += 1
            elif event.key == K_b:
                    mp.right_pitch += -1

            left_mirror_transform = carla.Transform(carla.Location(x=.7, y=-1, z=1.2), carla.Rotation(pitch=mp.left_pitch, yaw=mp.left_yaw))
            right_mirror_transform = carla.Transform(carla.Location(x=.7, y=1, z=1.2), carla.Rotation(pitch=mp.right_pitch,yaw=mp.right_yaw))
            lmv_sensor.set_transform(left_mirror_transform)
            rmv_sensor.set_transform(right_mirror_transform)


        # TODO - Get vehicle telemetry and post to shared memory
        '''
        #v = vehicle.get_velocity()
        #Speed = (3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2))
        #print (Speed)
        '''

   
print('Shutting Down')
client.apply_batch([carla.command.DestroyActor(x) for x in vehicle_list])
world.apply_settings(original_settings)
pygame.quit()
print ("Done")