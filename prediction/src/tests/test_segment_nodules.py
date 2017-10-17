import pytest
import numpy as np
from scipy.ndimage.measurements import label
from ..algorithms.segment import trained_model


@pytest.fixture
def dicom_path():
    yield '../images/LIDC-IDRI-0001/1.3.6.1.4.1.14519.5.2.1.6279.6001.298806137288633453246975630178/' \
          '1.3.6.1.4.1.14519.5.2.1.6279.6001.179049373636438705059720603192'


@pytest.fixture
def nodule_locations():
    yield [{"x": 187, "y": 217, "z": 7}, {"x": 317, "y": 367, "z": 7}]


def test_nodule_segmentation(dicom_path, nodule_locations):
    predictions = trained_model.predict(dicom_path, nodule_locations)

    mask = np.load(predictions["binary_mask_path"])

    assert np.sum(mask) > 0
    _, num_features = label(mask)
    assert num_features == 2
    assert len(predictions["volumes"]) == 2
    assert len(predictions["diameters"]) == 2
