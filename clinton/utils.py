def get_foia_url(path):
    """Join the FOIA URL root with the provided path.

    Arguments:
        path (str): The path to append to the base FOIA URL.

    Returns:
        str: The joined URL.
    """
    foia_url_root = 'https://foia.state.gov/searchapp/'
    url = foia_url_root + path.lstrip('/')

    return url
