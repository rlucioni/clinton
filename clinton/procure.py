import json
from time import time

import requests

from constants import PDF_ROOT, TXT_ROOT
from tasks import download
from utils import create_directories, get_foia_url, clean_timestamps


def get_metadata(records=1):
    """Retrieve metadata for the requested number of records.

    Keyword Arguments:
        records (int): The number of records for which to retrieve metadata.

    Returns:
        dict: The retrieved metadata.
    """
    url = get_foia_url('Search/SubmitSimpleQuery')
    params = {
        'collectionMatch': 'Clinton_Email',
        'searchText': '*',
        'beginDate': 'false',
        'endDate': 'false',
        'postedBeginDate': 'false',
        'postedEndDate': 'false',
        'caseNumber': 'false',
        'page': 1,
        'start': 0,
        'limit': records
    }

    # SSL certificate verification fails. To get around this,
    # ignore verification of the SSL certificate.
    response = requests.get(url, params=params, verify=False)

    text = clean_timestamps(response.text)
    data = json.loads(text)

    return data


def process(emails):
    """Process the provided dictionary of email data.

    Uses a Celery task to download emails and extract plain text, then stores 
    the resulting data in the database for later use.

    Arguments:
        emails (list of dict): A list of email metadata dictionaries.

    Returns:
        None
    """
    start = time()

    results = []
    for email in emails:
        results.append(download.delay(email))

    # TODO: Create email objects. Store all objects at once with add_all().
    for result in results:
        data = result.get()

    end = time()
    print "Complete in {} seconds.".format(end - start)


if __name__ == '__main__':
    create_directories(PDF_ROOT, TXT_ROOT)

    # Get total record count, then retrieve all records.
    data = get_metadata()
    total = data['totalHits']
    print "Processing {} emails...".format(total)
    data = get_metadata(records=total)

    emails = data['Results']
    process(emails)
