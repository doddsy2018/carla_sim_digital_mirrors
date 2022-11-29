import cv2
import numpy as np
from shared_memory_dict import SharedMemoryDict
from ruamel.yaml import YAML
from pathlib import Path
from screeninfo import get_monitors

smd = SharedMemoryDict(name='tokens', size=10000000)

# Read Config File
configfile=Path("config.yaml")
_config = YAML(typ='safe').load(configfile)

mirror_window_size=_config['sim']['windows']['mirror_res']

monitor=get_monitors()[0]
print (str(monitor))

no_img = np.zeros(shape=[mirror_window_size[1], mirror_window_size[0], 3], dtype=np.uint8)

while True:
    if 'left_mirror_view' in smd.keys():
        img = smd['left_mirror_view']
    else:
        img = no_img
    cv2.imshow("left Mirror", img)
    cv2.moveWindow("left Mirror", monitor.x, monitor.y)

    if 'right_mirror_view' in smd.keys():
        img = smd['right_mirror_view']
    else:
        img = no_img
    cv2.imshow("Right Mirror", img)
    cv2.moveWindow("Right Mirror", (monitor.width-mirror_window_size[0]-10),monitor.y)

    cv2.waitKey(1)
