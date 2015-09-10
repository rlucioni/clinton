import os
import re
from subprocess import call

from constants import PDF_ROOT, TXT_ROOT


def create_directories(*paths):
    """Create the requested directories.

    Arguments:
        *paths (str): Variable length argument list containing paths at which
            to create directories.

    Returns:
        None
    """
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)


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


def clean_timestamps(text):
    """Cleans timestamps in the provided text.

    The timestamp format used by the State Department is not valid JSON.

    Arguments:
        text (str): Text containing invalid timestamps.

    Returns:
        str: The input text with valid timestamps.
    """
    timestamp_pattern = r'new Date\(-?(?P<timestamp>[0-9]*)\)'
    text = re.sub(timestamp_pattern, '\g<timestamp>', text)

    return text


def get_filename(url):
    """Parse a filename from the given URL.

    Arguments:
        url (str): The file's URL.

    Returns:
        str: The extracted filename.
    """
    return url.split('/')[-1].split('.')[0]


def save_and_extract(filename, pdf):
    """Save the provided PDF and extract plain text from it.

    Arguments:
        filename (str): The filename to use when saving the PDF and text files.
        pdf (str): The PDF to save.

    Returns:
        tuple: The path to the saved PDF and the text extracted from it.
    """
    pdf_path = '{}/{}'.format(PDF_ROOT, filename + '.pdf')
    txt_path = '{}/{}'.format(TXT_ROOT, filename + '.txt')

    with open(pdf_path, 'w') as f:
        f.write(pdf)

    # Requires installation of the pdftotext command line utility
    call(['pdftotext', '-raw', pdf_path, txt_path])

    with open(txt_path) as f:
        text = f.read()

    return pdf_path, text
