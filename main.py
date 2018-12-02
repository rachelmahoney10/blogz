from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
import cgi

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogger@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')
    
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), unique=False) 
    body = db.Column(db.Text(), unique=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', pagetitle="Login")
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = User.query.filter_by(username=username)
        if users.count() == 1:
            user = users.first()
            if password == user.password:
                session['user'] = user.username
                flash('Welcome back, '+user.username+'!')
                return redirect("/newpost")
            else:
                flash('Your password was incorrect!')
        else:
            flash('No user found with that username!')
        return redirect("/login")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        user_count = User.query.filter_by(username=username).count()

        if username == '' or password == '' or verify == '':
            flash('All fields on this page are required')
            return redirect('/signup')
        user_db_count = User.query.filter_by(username=username).count()

        if User.query.filter_by(username=username).count() >0: #user_count > 0:
            flash('That username is already taken!')
            return redirect('/signup')

        if password != verify:
            flash('Passwords did not match!')
            return redirect('/signup')

        if len(password) < 4:
            flash('Password is too short!')
            return redirect('/signup')

        if len(username) < 4:
            flash('Username is too short!')
            return redirect('/signup')

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        session['user'] = user.username
        return redirect("/")
    else:
        return render_template('signup.html', pagetitle="Create an account")

@app.route("/logout", methods=['POST'])
def logout():
    del session['user']
    return redirect("/blog")


@app.route('/blog', methods=['GET', 'POST'])
def blog():
    posts = Blog.query.order_by('id DESC').all()
    blog_id = request.args.get('id')
    user_id = request.args.get('userid')

    if blog_id != None:
        post = Blog.query.filter_by(id=blog_id).first()
        print(post.title)
        print(post.body)
        return render_template('blog.html', blogid=post.id, title=post.title, body=post.body, owner=post.owner.username)

    if user_id != None:
        blogs = Blog.query.filter_by(owner_id=user_id).all()
        user = User.query.filter_by(id=user_id).first()
        return render_template('singleUser.html', posts=blogs, username=user.username, pagetitle=user.username+"'s Posts")

    return render_template('blog.html', posts=posts, pagetitle="Blogz")

@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        if title == "" and body == "":
            return render_template('newpost.html', pagetitle="New Post")

        if title == "":
            error = "Title can't be blank"
            return render_template('newpost.html', body=body, error_msg=error)

        if body == "":
            error = "Body can't be blank"
            return render_template('newpost.html', title=title, error_msg=error)

        newpost = Blog(title, body, logged_in_user())
        db.session.add(newpost)
        db.session.commit()
        lastid = Blog.query.order_by('id DESC').first()
        return redirect('/blog?id='+str(lastid.id))
    
    return render_template('newpost.html', pagetitle="New Post")


@app.route('/')
def index():
    users = User.query.order_by('username ASC').all()
    return render_template('index.html', users=users, pagetitle="Home")

def logged_in_user():
    owner = User.query.filter_by(username=session['user']).first()
    return owner

endpoints_without_login = ['index', 'login', 'signup', 'blog', 'css']

@app.before_request
def require_login():
    if not ('user' in session or request.endpoint in endpoints_without_login):
        flash('You must be logged in to complete that action!')
        return redirect('/login')

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RU'

if __name__ == "__main__":
    app.run()