# Clinton Emails

Tools to download and analyze emails provided by Hillary Clinton to the State Department.

### Context

​In December 2014, former Secretary Hillary Rodham Clinton provided the U.S. Department of State with emails that were sent or received by her while she was Secretary of State.

The State Department is in the midst of conducting a Freedom of Information Act (FOIA) review of all emails provided by former Secretary Clinton. Beginning in June 2015, a new corpus of emails from this collection will be published at the end of every month. These monthly releases are to continue until the entire corpus is reviewed for public release. All releasable records will be available as PDFs on the [FOIA site](https://foia.state.gov/Learn/New.aspx).

### Overview

The code contained in this repo can be used to download the PDFs distributed by the State Department, extract plain text from those PDFs, and store that text in a database for use when performing analysis.

To get started, create a new virtual environment and install the included requirements.

```
$ pip install -r requirements.txt
```

This project uses [Celery](http://celery.readthedocs.org/en/latest/) to asynchronously download the PDFs distributed by the State Department. Celery requires a solution to send and receive messages which typically comes in the form of a separate service called a message broker. This project uses [RabbitMQ](http://www.rabbitmq.com/) as a message broker. On OS X, use Homebrew to install it.

```
$ brew install rabbitmq
```

By default, most operating systems don't allow enough open files for a message broker. RabbitMQ's docs indicate that allowing at least 4096 file descriptors should be sufficient for most development workloads. Check the limit on the number of file descriptors in your current process by running:

```
$ ulimit -n
```

If it needs to be adjusted, run:

```
$ ulimit -n 4096
```

Next, start the RabbitMQ server.

```
$ rabbitmq-server
```

In a separate process, change into the `clinton` package and start the Celery worker.

```
$ cd clinton
$ celery -A clinton worker --app=celery_app:app --loglevel=info
```

In a third process, change into the `clinton` package and run the document procurement script. It takes about 10 minutes to download all 7,945 PDFs available as of the State Department's August release.

```
$ cd clinton
$ python procure.py
```

If you're forced to shut down the Celery workers prematurely, tasks may remain in the queue. To clear them, you can reset RabbitMQ.

```
$ rabbitmqctl stop_app
$ rabbitmqctl reset
$ rabbitmqctl start_app
```
