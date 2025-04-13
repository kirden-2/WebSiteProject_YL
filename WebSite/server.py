from flask import Flask, render_template
from data import db_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'


def main():
    db_session.global_init("db/database.db")
    app.run(port=5000, host='localhost')


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/artwork/<int:id>')
def artwork(id):
    return render_template('artwork.html')


@app.route('/authors')
def authors():
    return render_template('authors.html')


@app.route('/catalog')
def catalog():
    return render_template('catalog.html')


@app.route('/profile/<int:id>')
def profile(id):
    return render_template('profile.html')


if __name__ == '__main__':
    main()
