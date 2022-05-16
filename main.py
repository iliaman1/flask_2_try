import sqlite3 as sq
import os
from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g, make_response
from flsite import FDataBase

# конфигурация
DATABASE = '/tmp/flsite.db'
DEBUG = True
SECRET_KEY = 'abobus70000'

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))


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






@app.route("/")
@app.route('/index')
def index():
    db = get_db()
    dbase = FDataBase(db)
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
    db = get_db()
    dbase = FDataBase(db)
    print(url_for('about'))
    return render_template('about.html', title="О сайте", menu=dbase.getMenu())


@app.route("/profile/<username>")
def profile(username):
    if 'userLogged' not in session or session['userLogged'] != username:
        abort(401)
    return f"Пользователь: {username}"


@app.route("/contact", methods=["POST", "GET"])
def contact():
    db = get_db()
    dbase = FDataBase(db)
    if request.method == "POST":
        if len(request.form['username']) > 2:
            flash('Сообщение отправлено', category='success')
        else:
            flash('Ошибка отправки', category='error')
    return render_template('contact.html', title="Обратная связь", menu=dbase.getMenu())


@app.route('/add_post', methods=["POST", "GET"])
def addPost():
    db = get_db()
    dbase = FDataBase(db)

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
def showPost(alias):
    db = get_db()
    dbase = FDataBase(db)
    title, post = dbase.getPost(alias)
    if not title:
        abort(404)

    return render_template('post.html', menu=dbase.getMenu(), title=title, post=post)


@app.route("/login", methods=["POST", "GET"])
def login():
    db = get_db()
    dbase = FDataBase(db)
    log = ""
    # if request.cookies.get('logged'):
    #     log = request.cookies.get('logged')
    if 'userLogged' in session or request.cookies.get('logged') =='yes':
        return redirect(url_for('profile', username=session['userLogged']))
    elif request.method == 'POST' and request.form['username'] == "iliaman" and request.form['psw'] == "123":
        session['userLogged'] = request.form['username']
        content = redirect(url_for('profile', username=session['userLogged']))
        res = make_response(content)
        res.set_cookie("logged", "yes", 30*24*3600)
        return res
    return render_template('login.html', title='Авторизация', menu=dbase.getMenu())


@app.route("/logout")
def logout():
    res = make_response('Вы больше не авторизированы!')
    res.set_cookie("logged", "", 0)
    if session['userLogged']: del session['userLogged']
    return res


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
