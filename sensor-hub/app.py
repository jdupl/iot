from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMRY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)

    def __init__(self, value):
        self.value = value

@app.route('/', methods=['POST'])
def hub():
    data = request.data
    records = data.decode('utf-8').split('\n')
    for val in records:
        record = Record(val)
        db.session.add(record)
        db.session.commit()
    return 'ok'

if __name__ == '__main__':
    app.run()
