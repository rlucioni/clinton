from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Email(Base):
    __tablename__ = 'emails'

    id = Column(Integer, primary_key=True)
    sender = Column(String)
    recipient = Column(String)
    sent = Column(DateTime)
    subject = Column(String)
    body = Column(Text)

    # See http://www.sqlite.org/intern-v-extern-blob.html.
    pdf_path = Column(String)
    pdf_link = Column(String)
    pdf_posted = Column(DateTime)

    case_number = Column(String)
    document_class = Column(String)
    document_id = Column(String)

    def __repr__(self):
        return '<Email(sender={}, recipient={}, sent={}, subject={}, document_id={})>'.format(
            self.sender,
            self.recipient,
            self.sent,
            self.subject,
            self.document_id,
        )


engine = create_engine('sqlite:///clinton.sqlite')
Base.metadata.create_all(engine)
