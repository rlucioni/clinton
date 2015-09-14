from datetime import datetime
import requests
from subprocess import call

from celery_app import app
from constants import PDF_ROOT, TXT_ROOT
from utils import get_foia_url


@app.task()
def download(email):
    """Process the provided dictionary of email metadata.

    Download the corresponding PDF and extract plain text from it.

    Arguments:
        email (dict): A dictionary of email metadata. For example,
            {
                'from': 'H',
                'pdfLink': 'DOCUMENTS/HRCEmail_August_Web/IPS-0128/DOC_0C05775316/C05775316.pdf',
                'docDate': 1277956800000,
                'documentClass': 'Clinton_Email_August_Release',
                'messageNumber': '',
                'to': 'preines',
                'caseNumber': 'F-2014-20439',
                'subject': 'TEST',
                'originalLink': None,
                'postedDate': 1440993600000
            }

    Returns:
        dict: Containing the provided metadata, transformed if necessary,
            in addition to text from the downloaded PDF.
    """
    # TODO: These timestamps only give dates, not times. However, the emails
    # themselves contain dates and times. Extract these during stripping.
    email['sent'] = datetime_from_timestamp(email.pop('docDate'))
    email['pdf_posted'] = datetime_from_timestamp(email.pop('postedDate'))

    # TODO: Don't download the email if it's present on disk. Return None
    # so that a duplicate record isn't written to the database.
    url = get_foia_url(email.pop('pdfLink'))
    email['pdf_link'] = url

    # SSL certificate verification fails. To get around this,
    # ignore verification of the SSL certificate.
    response = requests.get(url, verify=False)
    pdf = response.content

    filename = get_filename(url)
    email['document_id'] = filename

    pdf_path, text = save_and_extract(filename, pdf)
    email['pdf_path'] = pdf_path
    email['body'] = text

    return email


def datetime_from_timestamp(timestamp):
    """Return a datetime object corresponding to the provided timestamp.

    Arguments:
        timestamp (int): A timestamp returned by the State Department.
    """
    return datetime.fromtimestamp(timestamp/1000)


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
    pdf_path = u'{}/{}'.format(PDF_ROOT, filename + '.pdf')
    txt_path = u'{}/{}'.format(TXT_ROOT, filename + '.txt')

    with open(pdf_path, 'w') as f:
        f.write(pdf)

    # Requires installation of the pdftotext command line utility
    call(['pdftotext', '-raw', pdf_path, txt_path])

    # TODO: Strip boilerplate text from emails, leaving only body.
    with open(txt_path) as f:
        text = f.read()
        text = text.decode('utf-8', 'ignore')

    return pdf_path, text
