import tempfile
_FILES = []


def get_temporary_file(suffix=None):
    """
    Creates a temporary file, and ensures that it is removed when the programs exits, but not before
    Args:
        suffix: Extension of the file to be created. Must include the dot if required

    Returns:
        A temporary file object

    """

    temporary_file = tempfile.NamedTemporaryFile(suffix=suffix)
    _FILES.append(temporary_file)
    return temporary_file
