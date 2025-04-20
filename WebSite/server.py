from flask import Flask, render_template, redirect, request, flash, url_for, abort
from sqlalchemy import or_

from data.category import Category
from data.arts import Arts
from data import db_session
from data.users import User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from data import __all_models

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}


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
    db_sess = db_session.create_session()
    if request.method == 'POST':
        name = request.form.get('name').strip()
        description = request.form.get('description').strip()
        short_description = request.form.get('short_description').strip()
        price = request.form.get('price').strip()
        category = request.form.get('category').strip()
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
        if not category:
            flash('У картины должно быть категория.')
            return render_template('add_artwork.html', **request.form)

        if not db_sess.query(Category).filter(Category.name == category).first():
            new_category = Category(name=category)
            db_sess.add(new_category)
            db_sess.commit()

        category = db_sess.query(Category).filter(Category.name == category).first()

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
        art.categories.append(category)
        db_sess.add(art)
        db_sess.commit()

        file_path = os.path.join('static/img', f'{art.id}{ext}')
        file.save(file_path)
        return redirect(url_for('profile', id=current_user.id))
    return render_template('add_artwork.html', categories=[category.name for category in db_sess.query(Category).all()])


@app.route('/authors')
def authors():
    return render_template('authors.html')


@app.route('/catalog', methods=['GET'])
def catalog():
    db_sess = db_session.create_session()
    query = db_sess.query(Arts).join(Arts.creator_user).join(Arts.categories)

    title = request.args.get('title')
    author = request.args.get('author')
    category = request.args.get('category')
    per_row = int(request.args.get('per_row')) if request.args.get('per_row') else 2

    if title:
        query = query.filter(Arts.name.ilike(f'%{title}%'))

    if author:
        query = query.filter(User.nick_name.ilike(f'%{author}%'))

    if category:
        query = query.filter(Category.name.ilike(f'%{category}%'))

    works = query.all()
    works_grouped = [works[i:i + per_row] for i in range(0, len(works), per_row)]

    return render_template('catalog.html',
                           works=works_grouped,
                           title=title,
                           author=author,
                           category=category,
                           per_row=per_row,
                           titles=[a.name for a in db_sess.query(Arts).all()],
                           authors=[u.nick_name for u in db_sess.query(User).all()],
                           categories=[c.name for c in db_sess.query(Category).all()])


@app.route('/profile/<int:id>')
def profile(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if not user:
        abort(404)
    if user.id == current_user.id:
        email = current_user.email
        balance = current_user.balance
    else:
        email = ''
        balance = ''
    works = db_sess.query(Arts).filter(or_(Arts.owner == user.id, Arts.creator == user.id)).all()
    works_owned = db_sess.query(Arts).filter(Arts.owner == user.id).all()
    works_created = db_sess.query(Arts).filter(Arts.creator == user.id).all()
    works_grouped = [works[i:i + 2] for i in range(0, len(works), 2)]
    works_owned_grouped = [works_owned[i:i + 2] for i in range(0, len(works_owned), 2)]
    works_created_grouped = [works_created[i:i + 2] for i in range(0, len(works_created), 2)]
    return render_template('profile.html',
                           email=email,
                           balance=balance,
                           user=user,
                           works_grouped=works_grouped,
                           works_owned_grouped=works_owned_grouped,
                           works_created_grouped=works_created_grouped)


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

        check_user = db_sess.query(User).filter(User.nick_name == nick_name).first()
        if not check_user or check_user.id == current_user.id:
            user.nick_name = nick_name
        else:
            flash('Имя уже используется')
            return render_template('settings.html')

        check_user = db_sess.query(User).filter(User.email == email).first()
        if not check_user or check_user.id == current_user.id or email == '':
            user.email = email
        else:
            flash('Почта уже используется')
            return render_template('settings.html')

        user.description = description

        if password and password == password_again:
            user.hashed_password = user.set_password(password)
        db_sess.commit()
        return redirect(url_for('profile', id=current_user.id))
    return render_template('settings.html')


@app.route('/edit_artwork/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_artwork(id):
    db_sess = db_session.create_session()
    work = db_sess.query(Arts).filter(Arts.id == id).first()
    categories = [category.name for category in db_sess.query(Category).all()]
    if not work:
        abort(404)
    if work.owner_user.id != current_user.id:
        abort(403)
    if request.method == 'POST':
        name = request.form.get('name').strip()
        description = request.form.get('description').strip()
        short_description = request.form.get('short_description').strip()
        price = request.form.get('price').strip()
        category = request.form.get('category').strip()

        if not price.isdigit():
            flash('Цена должна являться целым числом.')
            return render_template('edit_artwork.html', **request.form)

        if not db_sess.query(Category).filter(Category.name == category).first():
            new_category = Category(name=category)
            db_sess.add(new_category)
            db_sess.commit()

        work.name = name
        work.description = description
        work.short_description = short_description
        work.price = price
        work.categories = [db_sess.query(Category).filter(Category.name == category).first()]

        db_sess.commit()
        return redirect(url_for('profile', id=current_user.id))
    return render_template('edit_artwork.html', work=work, categories=categories)


@app.route('/delete_artwork/<int:id>', methods=['POST'])
@login_required
def delete_artwork(id):
    db_sess = db_session.create_session()
    work = db_sess.query(Arts).filter(Arts.id == id).first()
    if not work:
        abort(404)
    if work.owner_user.id != current_user.id:
        abort(403)
    file_path = os.path.join('static/img', f'{work.id}{work.extension}')
    os.remove(file_path)
    work.categories.clear()
    db_sess.delete(work)
    db_sess.commit()
    return redirect(url_for('profile', id=current_user.id))


@app.errorhandler(400)
def bad_request(e):
    return render_template('error400.html'), 400


@app.errorhandler(403)
def bad_request(e):
    return render_template('error403.html'), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error500.html'), 500


if __name__ == '__main__':
    main()
