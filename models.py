from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = 'clients'
    ac_no = Column(String(50), primary_key=True)
    bal = Column(String(50), unique=True)
    pin_no = Column(String(10), unique=True)

    def __init__(self, ac_no=None, pin_no=None, bal=None):
        self.ac_no = ac_no
        self.bal = bal
        self.pin_no = pin_no

    def __repr__(self):
        return '<User %r>' % (self.ac_no)