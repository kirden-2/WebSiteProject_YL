from flask import Flask, render_template, redirect, request, flash, url_for, abort
from sqlalchemy import or_, func, desc
from sqlalchemy.orm import joinedload

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
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        short_description = request.form.get('short_description', '').strip()
        price = request.form.get('price', '').strip()
        categories = request.form.get('categories', '').strip()
        file = request.files['image']

        if not file or file.filename == '':
            flash('В запросе отсутствует файл или его не удалось загрузить.')
            return render_template('add_artwork.html',
                                   **request.form,
                                   allCategories=[category.name for category in db_sess.query(Category).all()])

        if not check_extension(file.filename):
            flash('Данный формат файла не разрешён.')
            return render_template('add_artwork.html',
                                   **request.form,
                                   allCategories=[category.name for category in db_sess.query(Category).all()])

        if not name or not price:
            flash('Не все поля заполнены.')
            return render_template('add_artwork.html',
                                   **request.form,
                                   allCategories=[category.name for category in db_sess.query(Category).all()])
        if not price.isdigit() or int(price) < 0:
            flash('Цена должна являться целым положительным числом.')
            return render_template('add_artwork.html',
                                   **request.form,
                                   allCategories=[category.name for category in db_sess.query(Category).all()])

        c_names = [c.strip() for c in categories.split(',')]
        c_names = [c for c in c_names if c]

        if not c_names:
            flash('У картины должно быть категория.')
            return render_template('add_artwork.html',
                                   **request.form,
                                   allCategories=[category.name for category in db_sess.query(Category).all()])

        new_categories = []

        for c in c_names:
            cat = db_sess.query(Category).filter_by(name=c).first()
            if not cat:
                cat = Category(name=c)
                db_sess.add(cat)
            new_categories.append(cat)

        ext = os.path.splitext(file.filename)[1]
        art = Arts(
            name=name,
            description=description,
            short_description=short_description,
            price=int(price),
            creator=current_user.id,
            owner=current_user.id,
            extension=ext,
            categories=new_categories
        )
        db_sess.add(art)
        db_sess.commit()

        file_path = os.path.join('static/img/arts', f'{art.id}{ext}')
        file.save(file_path)
        return redirect(url_for('profile', id=current_user.id))
    return render_template('add_artwork.html',
                           allCategories=[category.name for category in db_sess.query(Category).all()])


@app.route('/authors', methods=['GET'])
def authors():
    db_sess = db_session.create_session()

    # Создаём список кортежей Автор, кол-во работ, Просмотры
    query = db_sess.query(
        User,
        # Берём кол-во, где данный юзер автор
        func.count(Arts.id).label('works_count'),
        # Берём сумму просмотров. coalesce позволяет избавится от NULL
        func.coalesce(func.sum(Arts.views), 0).label('total_views')
    ).join(Arts, User.id == Arts.creator).group_by(User.id)  # group_by обязательно (требуется для count/sum)

    author = request.args.get('author', '').strip()
    popular_filter = request.args.get('popularFilter', '')
    works_count_filter = request.args.get('worksCountFilter', '')

    a_names = []

    if author:
        a_names = [a.strip() for a in author.split(',')]
        a_names = set(a for a in a_names if a)
        exprs = [User.nick_name.ilike(f'%{aut}%') for aut in a_names]
        query = query.filter(or_(*exprs))

    result = []
    for user, count, views in query.all():
        result.append({
            'user': user,
            'works_count': count,
            'total_views': views,
            'popular_works': db_sess.query(Arts)
            .filter(Arts.creator == user.id)
            .order_by(desc(Arts.views))
            .limit(3)
            .all()
        })

    if popular_filter:
        result.sort(key=lambda x: x['total_views'], reverse=True)
    if works_count_filter:
        result.sort(key=lambda x: x['works_count'], reverse=True)

    return render_template('authors.html',
                           authors=result,
                           author=', '.join(a_names),
                           popularFilter=popular_filter,
                           worksCountFilter=works_count_filter,
                           allAuthors=[u.nick_name for u in db_sess.query(User).all()])


@app.route('/catalog', methods=['GET'])
def catalog():
    db_sess = db_session.create_session()
    query = db_sess.query(Arts).join(Arts.creator_user).join(Arts.categories)

    title = request.args.get('title', '').strip()
    author = request.args.get('author', '').strip()
    categories = request.args.get('categories', '').strip()
    top_filter = request.args.get('top_filter', '')

    t_names, a_names, c_names = [], [], []

    if title:
        t_names = [t.strip() for t in title.split(',')]
        t_names = set(t for t in t_names if t)
        exprs = [User.nick_name.ilike(f'%{tit}%') for tit in t_names]
        query = query.filter(or_(*exprs))

    if author:
        a_names = [a.strip() for a in author.split(',')]
        a_names = set(a for a in a_names if a)
        exprs = [User.nick_name.ilike(f'%{aut}%') for aut in a_names]
        query = query.filter(or_(*exprs))

    if categories:
        c_names = [c.strip() for c in categories.split(',')]
        c_names = set(c for c in c_names if c)
        exprs = [Category.name.ilike(f'%{cat}%') for cat in c_names]
        query = query.filter(or_(*exprs))

    works = query.all()

    if top_filter:
        works.sort(key=lambda x: x.views, reverse=True)

    return render_template('catalog.html',
                           works=works,
                           title=', '.join(t_names),
                           author=', '.join(a_names),
                           categories=', '.join(c_names),
                           top_filter=top_filter,
                           allTitles=[a.name for a in db_sess.query(Arts).all()],
                           allAuthors=[u.nick_name for u in db_sess.query(User).all()],
                           allCategories=[c.name for c in db_sess.query(Category).all()])


@app.route('/profile/<int:id>')
def profile(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if not user:
        abort(404)

    works = db_sess.query(Arts).filter(or_(Arts.owner == id, Arts.creator == id)).all()
    works_owned = [w for w in works if w.owner == id]
    works_created = [w for w in works if w.creator == id]

    works_grouped = [works[i:i + 2] for i in range(0, len(works), 2)]
    works_owned_grouped = [works_owned[i:i + 2] for i in range(0, len(works_owned), 2)]
    works_created_grouped = [works_created[i:i + 2] for i in range(0, len(works_created), 2)]

    if user.id == current_user.id:
        email = current_user.email
        balance = current_user.balance
    else:
        email = balance = ''
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
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()

    if request.method == 'POST':
        nick_name = request.form.get('nick_name', '').strip()
        email = request.form.get('email', '').strip()
        description = request.form.get('description', '').strip()
        password = request.form.get('password', '').strip()
        password_again = request.form.get('password_again', '').strip()
        avatar = request.files.get('avatar', '')
        card = request.files.get('card', '')

        if avatar and avatar.filename != '':
            if not check_extension(avatar.filename):
                flash('Данный формат изображения (аватар) не разрешён.')
                return render_template('settings.html', user=user)
            ext = os.path.splitext(avatar.filename)[1]
            avatar_path = os.path.join('static/img/avatars', f'{user.id}{ext}')
            avatar.save(avatar_path)
            user.avatar_ext = ext

        if card and card.filename != '':
            if not check_extension(card.filename):
                flash('Данный формат изображения (карточка) не разрешён.')
                return render_template('settings.html', user=user)
            ext = os.path.splitext(card.filename)[1]
            card_path = os.path.join('static/img/cards', f'{user.id}{ext}')
            card.save(card_path)
            user.card_ext = ext

        if nick_name and nick_name != user.nick_name:
            check_user = db_sess.query(User).filter(User.nick_name == nick_name).first()
            if check_user:
                flash('Имя уже используется')
                return render_template('settings.html', user=user)
            user.nick_name = nick_name

        if email and email != user.email:
            check_user = db_sess.query(User).filter(User.email == email).first()
            if check_user:
                flash('Почта уже используется')
                return render_template('settings.html', user=user)
            user.email = email

        if description != user.description:
            if len(description) > 1000:
                flash('Описание превысило максимальный порог символов')
                return render_template('settings.html', user=user)
            user.description = description

        if password:
            if password != password_again:
                flash('Пароли не совпадают')
                return render_template('settings.html', user=user)
            user.set_password(password)

        db_sess.commit()
        return redirect(url_for('profile', id=user.id))
    return render_template('settings.html', user=user)


@app.route('/edit_artwork/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_artwork(id):
    db_sess = db_session.create_session()
    work = db_sess.query(Arts).filter(Arts.id == id).first()
    if not work:
        abort(404)
    if work.owner_user.id != current_user.id:
        abort(403)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        short_description = request.form.get('short_description', '').strip()
        price = request.form.get('price', '').strip()
        categories = request.form.get('categories', '')

        if not price.isdigit() or int(price) < 0:
            flash('Цена должна являться целым положительным числом.')
            return render_template(
                'edit_artwork.html',
                work=work,
                allCategories=[category.name for category in db_sess.query(Category).all()],
                **request.form)
        if not all([name, price]):
            flash('Не все поля заполнены.')
            return render_template(
                'edit_artwork.html',
                work=work,
                allCategories=[category.name for category in db_sess.query(Category).all()],
                **request.form)

        c_names = [c.strip() for c in categories.split(',')]
        c_names = [c for c in c_names if c]

        if not c_names:
            flash('У картинки должна быть категория.')
            return render_template(
                'edit_artwork.html',
                work=work,
                allCategories=[category.name for category in db_sess.query(Category).all()],
                **request.form)

        new_categories = []

        for c in c_names:
            cat = db_sess.query(Category).filter_by(name=c).first()
            if not cat:
                cat = Category(name=c)
                db_sess.add(cat)
            new_categories.append(cat)

        work.name = name
        work.description = description
        work.short_description = short_description
        work.price = price
        work.categories = new_categories

        db_sess.commit()
        return redirect(url_for('profile', id=current_user.id))
    return render_template('edit_artwork.html',
                           work=work,
                           allCategories=[category.name for category in db_sess.query(Category).all()],
                           work_categories=', '.join([i.name for i in work.categories]))


@app.route('/delete_artwork/<int:id>', methods=['POST'])
@login_required
def delete_artwork(id):
    db_sess = db_session.create_session()
    work = db_sess.query(Arts).filter(Arts.id == id).first()
    if not work:
        abort(404)
    if work.owner_user.id != current_user.id:
        abort(403)
    file_path = os.path.join('static/img/arts', f'{work.id}{work.extension}')
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
