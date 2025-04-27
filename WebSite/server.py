from flask import Flask, render_template, redirect, request, flash, url_for

from data.arts import Arts
from data import db_session, bot_api
from data.users import User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}


def main():
    db_session.global_init("db/database.db")
    app.register_blueprint(bot_api.blueprint)
    app.run(port=5000, host='localhost')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
@app.route('/index')
def index():
    db_sess = db_session.create_session()
    top_3_works = sorted(db_sess.query(Arts).all(), key=lambda x: x.views, reverse=True)[:3]
    return render_template('index.html', works=top_3_works)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nick_name = request.form.get('nick_name')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me')

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.nick_name == nick_name).first()
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

        if not nick_name or not password:
            flash("Не все поля заполнены.")
            return render_template('register.html', nick_name=nick_name)
        if password != password_again:
            flash("Пароли не совпадают.")
            return render_template('register.html', nick_name=nick_name)
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.nick_name == nick_name).first():
            flash('Такое име уже используется')
            return render_template('register.html')

        user = User(
            nick_name=nick_name
        )
        user.set_password(password)
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=True)
        return redirect('/')
    return render_template('register.html')


@app.route('/purchase/<int:id>', methods=['POST'])
@login_required
def purchase(id):
    db_sess = db_session.create_session()
    work = db_sess.query(Arts).filter(Arts.id == id).first()
    user = db_sess.query(User).filter(User.id == current_user.id).first()

    if work.price > user.balance:
        flash('У вас недостаточно средств')
        return render_template('artwork.html', work=work)
    if work.price <= 0:
        flash('Данная работа не продаётся')
        return render_template('artwork.html', work=work)
    if work.owner == user.id:
        flash('Вы уже владеете этой работой')
        return render_template('artwork.html', work=work)

    work.owner = user.id
    user.balance -= work.price

    db_sess.commit()
    return render_template('artwork.html', work=work)


@app.route('/artwork/<int:id>')
def artwork(id):
    db_sess = db_session.create_session()
    work = db_sess.query(Arts).filter(Arts.id == id).first()
    return render_template('artwork.html', work=work)


def check_extension(filename):
    return os.path.splitext(filename)[1] in ALLOWED_EXTENSIONS


@app.route('/add_artwork', methods=['GET', 'POST'])
@login_required
def add_artwork():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        description = request.form.get('description').strip()
        short_description = request.form.get('short_description').strip()
        price = request.form.get('price').strip()
        file = request.files['image']

        if file.filename == '' or not file:
            flash('В запросе отсутствует файл или его не удалось загрузить.')
            return render_template('add_artwork.html', **request.form)

        if not check_extension(file.filename):
            flash('Данный формат файла не разрешён.')
            return render_template('add_artwork.html', **request.form)

        if not name or not price:
            flash('Не все поля заполнены.')
            return render_template('add_artwork.html', **request.form)
        if not price.isdigit():
            flash('Цена должна являться целым числом.')
            return render_template('add_artwork.html', **request.form)
        db_sess = db_session.create_session()
        ext = os.path.splitext(file.filename)[1]
        art = Arts(
            name=name,
            description=description,
            short_description=short_description,
            price=int(price),
            creator=current_user.id,
            owner=current_user.id,
            extension=ext
        )

        db_sess.add(art)
        db_sess.commit()

        file_path = os.path.join('static/img', f'{art.id}{ext}')
        file.save(file_path)
        return redirect(url_for('profile', id=current_user.id))
    return render_template('add_artwork.html')


@app.route('/authors')
def authors():
    return render_template('authors.html')


@app.route('/catalog')
def catalog():
    return render_template('catalog.html')


@app.route('/profile/<int:id>')
def profile(id):
    db_sess = db_session.create_session()
    works = db_sess.query(Arts).filter(Arts.owner == id).all()
    works_grouped = [works[i:i + 2] for i in range(0, len(works), 2)]
    return render_template('profile.html', works=works_grouped)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        nick_name = request.form.get('nick_name').strip()
        email = request.form.get('email').strip()
        description = request.form.get('description').strip()
        password = request.form.get('password').strip()
        password_again = request.form.get('password_again').strip()

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if nick_name:
            check_user = db_sess.query(User).filter(User.nick_name == nick_name).first()
            if not check_user or check_user.id == current_user.id:
                user.nick_name = nick_name
            else:
                flash('Имя уже используется')
                return render_template('settings.html')
        if email:
            check_user = db_sess.query(User).filter(User.email == email).first()
            if not check_user or check_user.id == current_user.id:
                user.email = email
            else:
                flash('Почта уже используется')
                return render_template('settings.html')
        if description:
            user.description = description
        if password and password == password_again:
            user.hashed_password = user.set_password(password)
        db_sess.commit()
        return redirect(url_for('profile', id=current_user.id))
    return render_template('settings.html')


if __name__ == '__main__':
    main()
