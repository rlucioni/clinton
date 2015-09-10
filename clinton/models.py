from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Email(Base):
    __tablename__ = 'emails'

    id = Column(Integer, primary_key=True)
    sender = Column(String)
    recipient = Column(String)
    subject = Column(String)
    body = Column(Text)
    sent = Column(DateTime)

    # See http://www.sqlite.org/intern-v-extern-blob.html.
    pdf_path = Column(String)
    pdf_link = Column(String)
    pdf_posted = Column(DateTime)

    case_number = Column(String)
    document_class = Column(String)


engine = create_engine('sqlite:///clinton.sqlite', echo=False)
Base.metadata.create_all(engine)
