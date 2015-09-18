import json
import os
import re
from time import time

import requests
from sqlalchemy.orm import sessionmaker

from constants import PDF_ROOT, TXT_ROOT
from models import Email, engine
from tasks import download
from utils import get_foia_url

Session = sessionmaker(bind=engine)
session = Session()


def get_records(count=1):
    """Retrieve the requested number of records.

    Keyword Arguments:
        count (int): The number of records to retrieve.

    Returns:
        dict: The retrieved records.
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
        'limit': count
    }

    # SSL certificate verification fails. To get around this,
    # ignore verification of the SSL certificate.
    response = requests.get(url, params=params, verify=False)

    text = clean_timestamps(response.text)
    records = json.loads(text)

    return records


def process_records(records):
    """Process the provided records.

    Uses a Celery task to download emails and extract plain text, then stores 
    the resulting data in the database for later use.

    Arguments:
        records (dict): Records retrieved from the State Department.

    Returns:
        None
    """
    print "Processing records..."
    start = time()

    results = []
    emails = records['Results']
    for email in emails:
        results.append(download.delay(email))

    emails = []
    for result in results:
        data = result.get()

        if data is not None:
            sender = data['from']
            recipient = data['to']
            sent = data['sent']
            subject = data['subject']
            body = data['body']
            pdf_path = data['pdf_path']
            pdf_link = data['pdf_link']
            pdf_posted = data['pdf_posted']
            case_number = data['caseNumber']
            document_class = data['documentClass']
            document_id = data['document_id']
            is_redacted = data['is_redacted']

            email = Email(
                sender=sender,
                recipient=recipient,
                sent=sent,
                subject=subject,
                body=body,
                pdf_path=pdf_path,
                pdf_link=pdf_link,
                pdf_posted=pdf_posted,
                case_number=case_number,
                document_class=document_class,
                document_id=document_id,
                is_redacted=is_redacted,
            )

            emails.append(email)

    # Bulk insert for improved performance.
    session.add_all(emails)
    session.commit()

    end = time()
    print "Complete in {} seconds.".format(end - start)


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


if __name__ == '__main__':
    create_directories(PDF_ROOT, TXT_ROOT)

    # Get total record count.
    records = get_records()
    count = records['totalHits']

    print "Retrieving {} records...".format(count)

    # Retrieve and process all records.
    records = get_records(count=count)
    process_records(records)
