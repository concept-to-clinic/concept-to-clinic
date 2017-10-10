import SimpleITK as sitk


def segment_nodule(image: sitk.Image, nodule: dict, lower_threshold=-600, upper_threshold=500, maximum_rms_error=0.02,
                   number_of_iterations=1000, curvature_scaling=0.5, radius=3):
    """
    Given an image and a nodule location, this function segments the nodule, using the
    ThresholdSegmentationLevelSetImageFilter from ITK.
    See https://itk.org/Doxygen/html/classitk_1_1SegmentationLevelSetImageFilter.html for further details on the Method

    Args:
      image: sitk.Image: Input Image
      nodule: dict: Nodule coordinates, in the form {"x": 1, "y": 1, "z": 1}
      lower_threshold:  Lower Hu threshold of the nodule to be segmented. Should be about the Hu of lung
                      (Default value = -600)
      upper_threshold: Upper Hu threshold of the nodule to be segmented. Should be less than the Hu of bone
                       (Default value = 500)
      maximum_rms_error: Stopping condition for the iterative solver.
      number_of_iterations: Maximum number of iterations to run
      curvature_scaling: Controls the smoothness of the contour. Higher value - smoother contour
      radius: Sets the radius of the initial segmentation around the nodule.

    Returns:
        mask: filepath to segmentation mask
        diameters: list of diameters
        volumes: list of  volumes

    """

    seed = (nodule["x"], nodule["y"], nodule["z"])
    # Create initial levelset based on the seed and the signed Maurer distance
    seg = sitk.Image(image.GetSize(), sitk.sitkUInt8)
    seg.CopyInformation(image)
    seg[seed] = 1
    # Binary dilate enlarges the seed mask by 3 pixels in all directions.
    seg = sitk.BinaryDilate(seg, radius)
    init_ls = sitk.SignedMaurerDistanceMap(seg, insideIsPositive=True, useImageSpacing=True)

    lsFilter = sitk.ThresholdSegmentationLevelSetImageFilter()
    # Sets the Hu value range for the nodule
    lsFilter.SetLowerThreshold(lower_threshold)
    lsFilter.SetUpperThreshold(upper_threshold)
    # Set stopping conditions
    lsFilter.SetMaximumRMSError(maximum_rms_error)
    lsFilter.SetNumberOfIterations(number_of_iterations)
    # CurvatureScaling controls how smooth the contour will be.
    lsFilter.SetCurvatureScaling(curvature_scaling)
    # PropagationScaling is also known as "balloon-force". Causes the segmented area to grow.
    lsFilter.SetPropagationScaling(1)
    lsFilter.ReverseExpansionDirectionOn()
    ls = lsFilter.Execute(init_ls, sitk.Cast(image, sitk.sitkFloat32))
    # Convert to binary mask
    mask = ls > 0

    # Calculate diameter and volume
    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.ComputeFeretDiameterOn()
    stats.SetBackgroundValue(0)
    stats.Execute(mask)
    diameter = stats.GetFeretDiameter(1)
    volume = stats.GetPhysicalSize(1)

    return mask, diameter, volume
