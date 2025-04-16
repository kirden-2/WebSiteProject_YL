from flask import Flask, render_template, redirect, request, flash

from data import db_session
from data.users import Users
from flask_login import LoginManager, login_user, logout_user, login_required

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/database.db")
    app.run(port=5000, host='localhost')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(Users).get(user_id)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nick_name = request.form.get('nick_name')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me')

        db_sess = db_session.create_session()
        user = db_sess.query(Users).filter(Users.nick_name == nick_name).first()
        if user and user.check_password(password):
            login_user(user, remember=True if remember_me else False)
            return redirect("/")
        flash('Неправильный логин или пароль')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nick_name = request.form.get('nick_name')
        password = request.form.get('password')
        password_again = request.form.get('password_again')

        if password != password_again:
            flash("Пароли не совпадают.")
            return render_template('register.html', nick_name=nick_name)
        db_sess = db_session.create_session()
        if db_sess.query(Users).filter(Users.nick_name == nick_name).first():
            flash('Такое име уже используется')
            return render_template('register.html')

        user = Users(
            nick_name=nick_name,
        )
        user.set_password(password)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
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
