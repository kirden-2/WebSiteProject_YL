from flask import Flask
from data import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'

def main():
    db_session.global_init("db/database.db")
    app.run(port=5000, host='localhost')

@app.route('/')
@app.route('/home')
def home():
    pass

if __name__ == '__main__':
    main()