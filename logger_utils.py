import multiprocessing as mp
import numpy as np
import h5py as h5
from config import *

LOGGER_MAX_FEATURES_RECORDS = LOGGER_DURATION * VIDEO_LOG_FRAMERATE
LOGGER_MAX_IMU_RECORDS = int(LOGGER_DURATION * IMU_OUT_DATA_RATE * 1.5)

logger_descriptors = np.zeros((LOGGER_MAX_FEATURES_RECORDS, ORB_DETECTOR_MAX_FEATURES, 32), dtype=np.float32)
logger_keypoints = np.zeros((LOGGER_MAX_FEATURES_RECORDS, ORB_DETECTOR_MAX_FEATURES, 2), dtype=np.float32)
logger_keypoints_len = np.zeros((LOGGER_MAX_FEATURES_RECORDS, 1), dtype=np.float32)
logger_dthe = np.zeros((LOGGER_MAX_IMU_RECORDS, 3), dtype=np.float32)


def logger(queue_imu: mp.Queue,
           queue_features: mp.Queue,
           stop: mp.Event):
    features_msg_counter = 0
    imu_msg_counter = 0

    while True:
        if stop.is_set():
            break
        if not queue_imu.empty():
            imu_msg = queue_imu.get()
            logger_dthe[imu_msg_counter, 0] = imu_msg.dthe[0]
            logger_dthe[imu_msg_counter, 1] = imu_msg.dthe[1]
            logger_dthe[imu_msg_counter, 2] = imu_msg.dthe[2]
            imu_msg_counter += 1
        if not queue_features.empty():
            features_msg = queue_features.get()
            logger_keypoints_len[features_msg_counter] = len(features_msg.points)
            for i in range(len(features_msg.points)):
                logger_keypoints[features_msg_counter, i, 0] = features_msg.points[i][0]
                logger_keypoints[features_msg_counter, i, 1] = features_msg.points[i][1]
                for j in range(32):
                    logger_descriptors[features_msg_counter, i, j] = features_msg.descriptors[i][j]
            features_msg_counter += 1
        if features_msg_counter >= LOGGER_MAX_FEATURES_RECORDS or imu_msg_counter >= LOGGER_MAX_IMU_RECORDS:
            stop.set()
            break

    log_file = h5.File('slam_log.h5', 'w')
    dset = log_file.create_dataset('outputs/dthe', data=logger_dthe[0:imu_msg_counter, :].T)
    dset = log_file.create_dataset('outputs/descriptors', data=logger_descriptors[0:features_msg_counter, :, :].T)
    dset = log_file.create_dataset('outputs/features', data=logger_keypoints[0:features_msg_counter, :, :].T)
    dset = log_file.create_dataset('outputs/features_len', data=logger_keypoints_len[0:features_msg_counter].T)
    log_file.close()
    print('Logger: Finished!')
