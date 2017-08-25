import numpy as np
import os
import pytest
import shutil

from ..algorithms.segment import trained_model


@pytest.fixture
def generate_motes(mask, centroid, volume):
    centroid_ = np.asarray([centroid['x'], centroid['y'], centroid['z']])
    free_voxels = np.where(mask != -1)
    free_voxels = np.asarray(free_voxels).T
    free_voxels = sorted(free_voxels, key=lambda x: np.linalg.norm(x - centroid_, ord=2))
    free_voxels = np.asarray(free_voxels[:volume]).T
    mask[(free_voxels[0], free_voxels[1], free_voxels[2])] = True
    

def generate_mask(shape, centroids, volumes):
    mask = np.zeros(shape, dtype=np.bool_)
    for centroid, volume in zip(centroids, volumes):
        generate_motes(mask, centroid, volume)
    return mask
    

def test_calculate_volume_on_unoverlapped_connected_components():
    centroids = [[0, 0, 0], [32, 32, 28], [45, 45, 12]]
    centroids = [{'x': centroid[0], 'y': centroid[1], 'z': centroid[2]} for centroid in centroids]
    mask = generate_mask(shape=[50, 50, 29], centroids=centroids, volumes=[100, 20, 30])
    assert mask.sum() == 150

    path = os.path.join('.', 'tmp', 'mask.npy')
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
#   The balls modelled to be not overlapped 
    np.save(path, mask)
    assert os.path.exists(path)
    
    volumes_calculated = trained_model.calculate_volume(path, centroids, voxel_shape=[1., 1., 1.])
    assert len(volumes_calculated) == 3
    assert volumes_calculated == [100, 20, 30]    
    shutil.rmtree(os.path.dirname(path))
    


def test_calculate_volume_on_overlapped_connected_components():
    centroids = [[0, 0, 0], [0, 0, 0], [45, 45, 12]]
    centroids = [{'x': centroid[0], 'y': centroid[1], 'z': centroid[2]} for centroid in centroids]
    mask = generate_mask(shape=[50, 50, 29], centroids=centroids, volumes=[100, 20, 30])
#   The balls area must be 100 + 30, since first ball have overlapped with the second one
    assert mask.sum() == 130
    
    path = os.path.join('.', 'tmp', 'mask.npy')

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    np.save(path, mask)
    assert os.path.exists(path)
    
    volumes_calculated = trained_model.calculate_volume(path, centroids, voxel_shape=[1., 1., 1.])
#   Despite they are overlapped, the amount of volumes must have preserved
    assert len(volumes_calculated) == 3
    assert volumes_calculated == [100, 100, 30]
    
    volumes_calculated = trained_model.calculate_volume(path, centroids, voxel_shape=[.5, 1., 1.5])
#   Despite they are overlapped, the amount of volumes must have preserved
    assert len(volumes_calculated) == 3
    assert volumes_calculated == [75., 75., 22.5]
    shutil.rmtree(os.path.dirname(path))