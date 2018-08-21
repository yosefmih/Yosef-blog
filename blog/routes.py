from flask import flash, redirect, render_template, url_for, request, abort
from blog import app
from blog.models import User, Post
from blog.form import LoginForm, RegistrationForm, UpdateAccountForm, PostForm, RequestResetForm, PasswordResetForm
from blog import db,bcrypt, mail,app
from flask_login import login_user, current_user, logout_user,login_required
import secrets
import os
from flask_mail import Message


    
@app.route('/index')
@app.route('/')
def home():
    page = request.args.get('page', 1, type = int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=2)
    return render_template("home.html", posts= posts)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data, email = form.email.data, password = hashed_pd)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in' , 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title = 'Register', form = form)


@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
            user = User.query.filter_by(email = form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember= form.remember.data)
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                else:
                    return redirect(url_for('home'))
            else:
                flash('Login unsuccessful. Please check email and password','danger')
    return render_template('login.html', title = 'Login', form = form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(img):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(img.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/pics', picture_fn)
    img.save(picture_path)
    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_fn = save_picture(form.picture.data)
            current_user.profile_pic = picture_fn
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!','success')
        return redirect(url_for('account'))
    elif request.method=="GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    profile_pic = url_for('static',filename= 'pics/'+current_user.profile_pic)
    return render_template('account.html', title = 'Account', profile_pic = profile_pic, form = form)

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content= form.content.data, author = current_user)
        db.session.add(post)
        db.session.commit()
        flash ('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', legend = "New Post", form=form)


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods= ['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
         post.title = form.title.data
         post.content = form.content.data
         db.session.commit()
         flash('Your post has been updated!', 'success')
         return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title = "Update_post", legend = "Update Post", form=form)

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403) 
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))    


@app.route("/user/<string:username>")
def userPosts(username):
    page = request.args.get('page', 1, type = int)
    user = User.query.filter_by(username = username).first_or_404()
    posts = Post.query.filter_by(author = user).order_by(Post.date_posted.desc()).paginate(page = page, per_page = 2)
    return render_template('userPosts.html', posts = posts, user=user)

def send_reset_email(user):
    token  = user.get_reset_token()
    msg = Message('Password Reset Request', sender = 'noreply@demo.com', 
                  recipients = [user.email])
    msg.body = f''' To reset your password, visit the following link:
        {url_for('resetPassword', token = token, _external = True)} 
         If you did not make this request then simply ignore this email and no change will occur. 
        '''

    mail.send(msg) 
@app.route("/password_reset", methods = ['GET', 'POST'])
def resetRequest():
    if current_user.is_authenticated:
          return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        send_reset_email(user)
        flash('An email has been set with instructions to reset your password.','info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title = 'Reset Password', form = form )


@app.route("/password_reset/<token>", methods = ['GET', 'POST'])
def resetPassword(token):
    if current_user.is_authenticated:
          return redirect(url_for('home'))
    user = User.verify_reset_token(token) 
    if not user:
        flash('The link is invalid or has expired', 'warning')
        return redirect(url_for('resetRequest'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        hashed_pd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_pd
        db.session.commit()
        flash('Your password has been updated successfully!' , 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title = 'Reset Password', form = form )