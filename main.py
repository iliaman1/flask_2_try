import sqlite3 as sq
import os
from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g, make_response
from flsite import FDataBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin
from forms import LoginForm

# конфигурация
DATABASE = '/tmp/flsite.db'
DEBUG = True
SECRET_KEY = 'abobus70000'
MAX_CONTENT_LENGTH = 1024 * 1024

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизируйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"

@login_manager.user_loader
def load_user(user_id):
    print("load_user")
    return UserLogin().fromDB(user_id, dbase)

def create_db():
    """Вспомогательная функция для создания БД"""
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
        db.commit()
        db.close()


def connect_db():
    conn = sq.connect(app.config['DATABASE'])
    conn.row_factory = sq.Row
    return conn


def get_db():
    '''Соединение с БД если оно еще не установлено'''
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
        return g.link_db


app.config['SECRET_KEY'] = 'abobys'


# menu = [{"name": "Установка", "url": "install-flask"},
#         {"name": "Первое приложение", "url": "first-app"},
#         {"name": "Обратная связь", "url": "contact"},
#         {"name": "Авторизация", "url": "login"}]

@app.errorhandler(404)
def pageNotFound(error):
    #трэба добавить возможность подгружать меню из бд пока не получается выдает ексепшон в ексепшоне хех
    # db = get_db()
    # dbase = FDataBase(db)
    return render_template('page404.html', title='Страница не найдена')


dbase = None
@app.before_request
def before_request():
    '''Установка соединения с бд перед выполнением запроса'''
    global dbase
    db = get_db()
    dbase = FDataBase(db)



@app.route("/")
@app.route('/index')
def index():
    if 'visits' in session:
        session['visits'] = session.get('visits')+1
    else:
        session['visits'] = 1
    content = render_template('index.html', menu=dbase.getMenu(), posts=dbase.getPostsAnonce(), visits=f"Число просмотров: {session['visits']}")
    res = make_response(content)
    res.headers['Content-Type'] = 'text/html'
    res.headers['Server'] = 'flasksite'
    return res


@app.route("/about")
def about():
    print(url_for('about'))
    return render_template('about.html', title="О сайте", menu=dbase.getMenu())


# @app.route("/profile/<username>")
# def profile(username):
#     if 'userLogged' not in session or session['userLogged'] != username:
#         abort(401)
#     return f"Пользователь: {username}"


@app.route("/contact", methods=["POST", "GET"])
def contact():
    if request.method == "POST":
        if len(request.form['username']) > 2:
            flash('Сообщение отправлено', category='success')
        else:
            flash('Ошибка отправки', category='error')
    return render_template('contact.html', title="Обратная связь", menu=dbase.getMenu())


@app.route('/add_post', methods=["POST", "GET"])
def addPost():

    if request.method == 'POST':
        if len(request.form['name']) > 4 and len(request.form['post']) > 10:
            res = dbase.addPost(request.form['name'], request.form['post'], request.form['url'])
            if not res:
                flash('Ошибка добавления статьи', category='error')
            else:
                flash('Статья добавлена успешно', category='success')
        else:
            flash('Ошибка добавления статьи', category='error')
    return render_template('add_post.html', menu=dbase.getMenu(), title='Добавление статьи')


@app.route('/post/<alias>')
@login_required
def showPost(alias):
    title, post = dbase.getPost(alias)
    if not title:
        abort(404)

    return render_template('post.html', menu=dbase.getMenu(), title=title, post=post)


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = dbase.getUserByEmail(form.email.data)
        if user and check_password_hash(user['psw'], form.psw.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            return redirect(request.args.get('next') or url_for('profile'))
        flash("Неверная пара логин/пароль", "error")
    return render_template("login.html", menu=dbase.getMenu(), title="Авторизация", form=form)

    # if request.method == "POST":
    #     user = dbase.getUserByEmail(request.form['email'])
    #     if user and check_password_hash(user['psw'], request.form['psw']):
    #         userlogin = UserLogin().create(user)
    #         rm = True if request.form.get('remainme') else False
    #         login_user(userlogin, remember=rm)
    #         return redirect(request.args.get('next') or url_for('profile'))
    #
    #     flash("Неверная пара логин/пароль", "error")

    # return render_template('login.html', title='Авторизация', menu=dbase.getMenu())
    # log = ""
    # if request.cookies.get('logged'):
    #     log = request.cookies.get('logged')
    # if 'userLogged' in session or request.cookies.get('logged') =='yes':
    #     return redirect(url_for('profile', username=session['userLogged']))
    # elif request.method == 'POST' and request.form['username'] == "iliaman" and request.form['psw'] == "123":
    #     session['userLogged'] = request.form['username']
    #     content = redirect(url_for('profile', username=session['userLogged']))
    #     res = make_response(content)
    #     res.set_cookie("logged", "yes", 30*24*3600)
    #     return res
    # return render_template('login.html', title='Авторизация', menu=dbase.getMenu())


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        if len(request.form['name'])>4 and len(request.form['email']) > 4 and len(request.form['psw'])>4 and request.form['psw'] == request.form['psw2']:
            hash = generate_password_hash(request.form['psw'])
            res = dbase.addUser(request.form['name'], request.form['email'], hash)
            if res:
                flash("Вы успешно зарегестрированы", "success")
                return redirect(url_for('login'))
            else:
                flash("Ошибка при добавлении в БД", "error")
        else:
            flash("Неверно заполнены поля", "error")
    return render_template("register.html", menu=dbase.getMenu(), title="Регистрация")


@app.route("/profile")
@login_required
def profile():
    res = current_user.get_id()
    return render_template("profile.html", menu=dbase.getMenu(), title="Профиль", info=res)


@app.route("/userava")
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""

    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


@app.route('/upload', methods=['POST', 'GET'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
                res = dbase.updateUserAvatar(img, current_user.get_id())
                if not res:
                    flash("Ошибка обновления аватара", "error")
                flash("Аватар обновлен", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка обновления аватара", "error")

    return redirect(url_for('profile'))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.teardown_appcontext
def close_db(error):
    '''Закрываем соединение с БД, если оно было установлено'''
    if hasattr(g, 'link_db'):
        g.link_db.close()


if __name__ == '__main__':
    app.run(debug=True)

# дегустируем url без запуска сервера(искуственно создаем контекст запроса)
# with app.test_request_context():
#     print(url_for('about'))
#     print(url_for('profile', username = "iliaman"))
