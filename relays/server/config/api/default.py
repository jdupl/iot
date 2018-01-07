import os
basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
HOST = '127.0.0.1'
PORT = 5002
DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'dev.sqlite')
SQLALCHEMY_TRACK_MODIFICATIONS = False
