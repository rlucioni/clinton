import requests

from celery_app import app
from utils import get_foia_url, get_filename, save_and_extract


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
        dict: Containing the provided metadata in addition to the downloaded
            PDF and the extracted plain text.
    """
    # TODO: Don't download the email if it's present on disk.
    url = get_foia_url(email.pop('pdfLink'))
    email['pdf_link'] = url

    # SSL certificate verification fails. To get around this,
    # ignore verification of the SSL certificate.
    response = requests.get(url, verify=False)
    pdf = response.content

    filename = get_filename(url)
    pdf_path, text = save_and_extract(filename, pdf)

    email['pdf_path'] = pdf_path
    email['body'] = text

    return email
