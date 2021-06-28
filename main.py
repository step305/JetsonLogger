import multiprocessing as mp
from camera_utils import camera_reader, video_recorder
from logger_utils import logger
from imu_utils import imu_reader
import time
from config import *


if __name__ == '__main__':
    queue_features = mp.Manager().Queue(MAX_QUEUE_LEN)
    queue_record = mp.Manager().Queue(MAX_QUEUE_LEN)
    queue_imu = mp.Manager().Queue(MAX_QUEUE_LEN)
    stop = mp.Event()

    logger_proc = mp.Process(target=logger, args=(queue_imu,
                                                  queue_features,
                                                  stop), daemon=True)

    recorder_proc = mp.Process(target=video_recorder, args=(queue_record,
                                                            stop), daemon=True)

    camera_proc = mp.Process(target=camera_reader, args=(queue_features,
                                                         queue_record,
                                                         stop), daemon=True)

    imu_proc = mp.Process(target=imu_reader, args=(queue_imu,
                                                   stop), daemon=True)

    logger_proc.start()
    recorder_proc.start()
    camera_proc.start()
    imu_proc.start()
    while True:
        if stop.is_set():
            break
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
    stop.set()
    time.sleep(0.1)
    camera_proc.terminate()
    imu_proc.terminate()
    recorder_proc.terminate()
    logger_proc.terminate()
    print('Exiting...')
    exit(0)
