# -*- coding: utf-8 -*-
"""
    algorithms.segment.trained_model
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    An API for a trained segmentation model to predict nodule boundaries and
    descriptive statistics.
"""
import numpy as np
import os
import scipy.ndimage


def predict(dicom_path, centroids):
    """ Predicts nodule boundaries.
    Given a pth to a DICOM image and a list of centroids
        (1) load the segmentation model from its serialized state
        (2) pre-process the dicom data into whatever format the segmentation
            model expects
        (3) for each pixel create an indicator 0 or 1 of if the pixel is
            cancerous
        (4) write this binary mask to disk, and return the path to the mask
    Args:
        dicom_path (str): a path to a DICOM directory
        centroids (list[dict]): A list of centroids of the form::
            {'x': int,
             'y': int,
             'z': int}
    Returns:
        dict: Dictionary containing path to serialized binary masks and
            volumes per centroid with form::
            {'binary_mask_path': str,
             'volumes': list[float]}
    """
    segment_path = 'path/to/segmentation'
    volumes = calculate_volume(segment_path, centroids)
    return_value = {
        'binary_mask_path': segment_path,
        'volumes': volumes
    }
    return return_value


def calculate_volume(segment_path, centroids, voxel_shape=1.):
    """ Calculates tumor volume.

    Given the path to the serialized mask and a list of centroids
        (1) For each centroid, calculate the volume of the tumor.  
        (2) DICOM has voxels' sizes in mm therefore the volume should be in real 
        measurements (not pixels).

    Args:
        segment_path (str): a path to a mask file
        centroids (list[dict]): A list of centroids of the form::
            {'x': int,
             'y': int,
             'z': int}
        voxel_shape (float | list[float]): The voxels' sizes along the axes. 
            If a float, `voxel_shape` is the same for each axis. 
            If a sequence, `voxel_shape` should contain one value for each axis.

    Raises: 
        TypeError, ValueError
            
    Returns:
        list[float]: a list of volumes of a connected component for each centroid
    """

    if not (isinstance(voxel_shape, float) or isinstance(voxel_shape, list)):
        raise TypeError('Type of voxel_shape should be float or list of floats.')

    try:
        mask = np.load(segment_path)
    except:
        raise ValueError('The segment_path must be a path to a numpy array.')        

        
    voxel_shape = scipy.ndimage._ni_support._normalize_sequence(voxel_shape, mask.ndim)
    mask, _ = scipy.ndimage.label(mask)
    labels = [mask[centroid['x'], centroid['y'], centroid['z']] for centroid in centroids]
    volumes = np.bincount(mask.flatten())
    volumes = volumes[labels] * np.prod(voxel_shape)
    return volumes.tolist()
