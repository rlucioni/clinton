from datetime import datetime
from subprocess import call

from fuzzywuzzy import fuzz
import requests

from celery_app import app
from constants import PDF_ROOT, TXT_ROOT
from utils import get_foia_url

INTERESTING_SENDERS = (
    'H',
    'hrod17@clintonemail.com',
)

STOPWORDS = (
    'UNCLASSIFIED',
    'RELEASE IN',
    'B6',
    'From:',
    'Sent:',
    'To:',
    'ReplyTo:',
    'Subject:',
    'Original Message',
    'Cc:',
    'Bcc:',
    '\x0c'
)


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
    if email['from'] not in INTERESTING_SENDERS:
        return

    # TODO: These timestamps only give dates, not times. However, the emails
    # themselves contain dates and times. Extract these.
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
    
    body, is_redacted = get_body(text)
    email['body'] = body
    email['is_redacted'] = is_redacted

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

    with open(txt_path) as f:
        text = f.read()
        text = text.decode('utf-8', 'ignore')

    return pdf_path, text


def get_content(text):
    """Parse interesting content from raw email text.

    Arguments:
        text (str): The text from which to parse interesting content.

    Returns:
        tuple: The cleaned text, a Boolean indicating whether the email was
            redacted.
    """
    body = []
    lines = text.split('\n')
    is_redacted = False

    for line in lines:
        for stopword in STOPWORDS:
            if startswith_fuzzy(stopword, line):
                if line == 'RELEASE IN PART':
                    is_redacted = True

                break
        else:
            body.append(line)
    body = ' '.join(body)

    return body, is_redacted


def startswith_fuzzy(phrase, line, tolerance=90):
    """Fuzzy startswith implementation.

    Determines if the provided line can be reasonably assumed to
    begin with the provided phrase.

    Arguments:
        phrase (str): A phrase.
        line (str): A line of text.

    Keyword Arguments:
        tolerance (int): If the fuzz ratio is greater than or
            equal to this tolerance value, the provided line
            can be reasonably assumed to begin with the provided phrase.

    Returns:
        Boolean, indicating if the line can be reasonably assumed
            to start with the provided phrase.
    """
    length = len(phrase)
    ratio = fuzz.ratio(phrase, line[:length])

    startswith = True if ratio < tolerance else False

    return startswith
