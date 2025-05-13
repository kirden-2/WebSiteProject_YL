from flask import Flask, render_template, redirect, request, flash, url_for, abort
from sqlalchemy import or_, func, desc
from flask_restful import Api

from WebSite.data.art_views import ArtView
from config import SECRET_KEY, ALLOWED_EXTENSIONS
from WebSite.data.category import Category
from WebSite.data.arts import Arts
from WebSite.data import db_session
from WebSite.resource import bot_api
from WebSite.data.users import User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os

app = Flask(__name__, static_folder=os.path.abspath("WebSite/static"))
app.config['SECRET_KEY'] = SECRET_KEY

api_bot = Api(app, prefix='/bot_api')

api_bot.add_resource(bot_api.RegisterResource, '/register')
api_bot.add_resource(bot_api.LoginResource, '/login')
api_bot.add_resource(bot_api.LogoutResource, '/logout')
api_bot.add_resource(bot_api.CheckBotLoginResource, '/login/check_bot_login')
api_bot.add_resource(bot_api.ArtsResource, '/arts/<int:art_id>', '/arts')
api_bot.add_resource(bot_api.UserInfoResource, '/user_info')
api_bot.add_resource(bot_api.ChangePasswordResource, '/change_account_data/password')
api_bot.add_resource(bot_api.ChangeEmailResource, '/change_account_data/email')
api_bot.add_resource(bot_api.ChangeDescriptionResource, '/change_account_data/description')
api_bot.add_resource(bot_api.AddArtResource, '/arts/add_artwork')
api_bot.add_resource(bot_api.ViewOwnedArts, '/owned_arts')
api_bot.add_resource(bot_api.PurchaseArt, '/purchase/<int:art_id>')

login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
@app.route('/index')
def index():
    db_sess = db_session.create_session()
    top_3 = db_sess.query(Arts).order_by(desc(Arts.views)).limit(3).all()
    return render_template('index.html', works=top_3)


@app.route('/login', methods=['GET', 'POST'])
def web_login():
    if request.method == 'POST':
        nick_name = request.form.get('nick_name', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember_me'))

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter_by(nick_name=nick_name).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            return redirect("/")
        flash('Неправильный логин или пароль')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def web_register():
    if request.method == 'POST':
        nick_name = request.form.get('nick_name', '').strip()
        password = request.form.get('password', '')
        password_again = request.form.get('password_again', '')

        if not nick_name or not password:
            flash("Не все поля заполнены.")
            return render_template('register.html', nick_name=nick_name)
        if password != password_again:
            flash("Пароли не совпадают.")
            return render_template('register.html', nick_name=nick_name)

        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.nick_name == nick_name).first():
            flash('Имя уже используется')
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


@app.route('/purchase/<int:art_id>', methods=['POST'])
@login_required
def purchase(art_id):
    db_sess = db_session.create_session()
    work = db_sess.query(Arts).get(art_id)
    user = db_sess.query(User).get(current_user.id)

    if not work:
        abort(404)

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


@app.route('/artwork/<int:art_id>')
def artwork(art_id):
    db_sess = db_session.create_session()
    work = db_sess.query(Arts).get(art_id)
    if not work:
        abort(404)

    if current_user.is_authenticated:
        already_viewed = db_sess.query(ArtView).filter_by(
            user_id=current_user.id,
            art_id=art_id
        ).first()
        if not already_viewed:
            work.views += 1
            db_sess.add(ArtView(user_id=current_user.id, art_id=art_id))
            db_sess.commit()

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
        upload_file = request.files.get('image')

        if not upload_file or upload_file.filename == '':
            flash('Файл не загружен')
            return render_template('add_artwork.html',
                                   **request.form,
                                   allCategories=[category.name for category in db_sess.query(Category).all()])

        if not check_extension(upload_file.filename):
            flash('Неподдерживаемый формат')
            return render_template('add_artwork.html',
                                   **request.form,
                                   allCategories=[category.name for category in db_sess.query(Category).all()])

        if not name or not price:
            flash('Не все поля заполнены')
            return render_template('add_artwork.html',
                                   **request.form,
                                   allCategories=[category.name for category in db_sess.query(Category).all()])

        if not price.isdigit() or int(price) < 0:
            flash('Цена должна являться целым положительным числом.')
            return render_template('add_artwork.html',
                                   **request.form,
                                   allCategories=[category.name for category in db_sess.query(Category).all()])

        cat_names = set(c.strip() for c in categories.split(',') if c.strip())

        if not cat_names:
            flash('Укажите хотя бы одну категорию')
            return render_template('add_artwork.html',
                                   **request.form,
                                   allCategories=[category.name for category in db_sess.query(Category).all()])

        categories = []

        for c in cat_names:
            cat = db_sess.query(Category).filter_by(name=c).first()
            if not cat:
                cat = Category(name=c)
                db_sess.add(cat)
            categories.append(cat)

        ext = os.path.splitext(upload_file.filename)[1]
        art = Arts(
            name=name,
            description=description,
            short_description=short_description,
            price=int(price),
            creator=current_user.id,
            owner=current_user.id,
            extension=ext,
            categories=categories
        )
        db_sess.add(art)
        db_sess.commit()

        file_path = os.path.join('WebSite/static/img/arts', f'{art.id}{ext}')
        upload_file.save(file_path)
        return redirect(url_for('profile', user_id=current_user.id))
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

    popular_filter = bool(request.args.get('popularFilter', ''))
    works_count_filter = bool(request.args.get('worksCountFilter', ''))

    authors = set(a.strip() for a in request.args.get('author', '').strip().split(',') if a.strip())
    if authors:
        exprs = [User.nick_name.ilike(f'%{aut}%') for aut in authors]
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
                           author=', '.join(authors),
                           popularFilter=popular_filter,
                           worksCountFilter=works_count_filter,
                           allAuthors=[u.nick_name for u in db_sess.query(User).all()])


@app.route('/catalog', methods=['GET'])
def catalog():
    db_sess = db_session.create_session()
    query = db_sess.query(Arts).join(Arts.creator_user).join(Arts.categories)

    filters = []

    titles = set(t.strip() for t in request.args.get('title', '').split(',') if t.strip())
    if titles:
        filters.append(or_(*[Arts.name.ilike(f'%{t}%') for t in titles]))

    authors = set(a.strip() for a in request.args.get('author', '').split(',') if a.strip())
    if authors:
        filters.append(or_(*[User.nick_name.ilike(f'%{a}%') for a in authors]))

    cats = set(c.strip() for c in request.args.get('categories', '').split(',') if c.strip())
    if cats:
        filters.append(or_(*[Category.name.ilike(f'%{c}%') for c in cats]))

    if filters:
        query = query.filter(*filters)

    works = query.all()

    if request.args.get('top_filter'):
        works.sort(key=lambda w: w.views, reverse=True)

    return render_template(
        'catalog.html',
        works=works,
        title=', '.join(titles),
        author=', '.join(authors),
        categories=', '.join(cats),
        top_filter=request.args.get('top_filter', ''),
        allTitles=[a.name for a in db_sess.query(Arts).all()],
        allAuthors=[u.nick_name for u in db_sess.query(User).all()],
        allCategories=[c.name for c in db_sess.query(Category).all()]
    )


@app.route('/profile/<int:user_id>')
def profile(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)

    if not user:
        abort(404)

    works = db_sess.query(Arts).filter(or_(Arts.owner == user_id, Arts.creator == user_id)).all()
    works_owned = [w for w in works if w.owner == user_id]
    works_created = [w for w in works if w.creator == user_id]

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
    user = db_sess.query(User).get(current_user.id)

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
            avatar_path = os.path.join('WebSite/static/img/avatars', f'{user.id}{ext}')
            avatar.save(avatar_path)
            user.avatar_ext = ext

        if card and card.filename != '':
            if not check_extension(card.filename):
                flash('Данный формат изображения (карточка) не разрешён.')
                return render_template('settings.html', user=user)
            ext = os.path.splitext(card.filename)[1]
            card_path = os.path.join('WebSite/static/img/cards', f'{user.id}{ext}')
            card.save(card_path)
            user.card_ext = ext

        if nick_name and nick_name != user.nick_name:
            if db_sess.query(User).filter(User.nick_name == nick_name).first():
                flash('Имя уже используется')
                return render_template('settings.html', user=user)
            user.nick_name = nick_name

        if email and email != user.email:
            if db_sess.query(User).filter(User.email == email).first():
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
        return redirect(url_for('profile', user_id=user.id))
    return render_template('settings.html', user=user)


@app.route('/edit_artwork/<int:art_id>', methods=['GET', 'POST'])
@login_required
def edit_artwork(art_id):
    db_sess = db_session.create_session()
    work = db_sess.query(Arts).get(art_id)
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
            flash('Цена должна являться целым положительным числом')
            return render_template(
                'edit_artwork.html',
                work=work,
                allCategories=[category.name for category in db_sess.query(Category).all()],
                **request.form)
        if not all([name, price]):
            flash('Не все поля заполнены')
            return render_template(
                'edit_artwork.html',
                work=work,
                allCategories=[category.name for category in db_sess.query(Category).all()],
                **request.form)

        cat_names = set(c.strip() for c in categories.split(',') if c.strip())

        if not cat_names:
            flash('Укажите хотя бы одну категорию')
            return render_template(
                'edit_artwork.html',
                work=work,
                allCategories=[category.name for category in db_sess.query(Category).all()],
                **request.form)

        new_categories = []

        for c in cat_names:
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
        return redirect(url_for('profile', user_id=current_user.id))
    return render_template('edit_artwork.html',
                           work=work,
                           allCategories=[category.name for category in db_sess.query(Category).all()],
                           work_categories=', '.join([i.name for i in work.categories]))


@app.route('/delete_artwork/<int:art_id>', methods=['POST'])
@login_required
def delete_artwork(art_id):
    db_sess = db_session.create_session()
    work = db_sess.query(Arts).get(art_id)
    if not work:
        abort(404)
    if work.owner_user.id != current_user.id:
        abort(403)
    file_path = os.path.join('WebSite/static/img/arts', f'{work.id}{work.extension}')
    os.remove(file_path)
    work.categories.clear()
    db_sess.delete(work)
    db_sess.commit()
    return redirect(url_for('profile', user_id=current_user.id))


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
    db_session.global_init("db/database.db")
    app.run(port=5000, host='localhost', debug=True)
