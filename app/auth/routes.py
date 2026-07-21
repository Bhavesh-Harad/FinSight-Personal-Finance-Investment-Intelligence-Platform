import os
import secrets
from threading import Thread
from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, current_app
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from app import db, bcrypt, mail, oauth
from app.models import User
from app.auth.forms import RegistrationForm, LoginForm, UpdateProfileForm, RequestResetForm, ResetPasswordForm, ChangePasswordForm
from functools import wraps

auth = Blueprint('auth', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error sending email: {e}")

def send_verification_email(user_data):
    token = User.get_registration_token(user_data)
    msg = Message('Verify Your FinSight Account',
                  recipients=[user_data['email']])
    msg.body = f'''To verify your account, visit the following link:
{url_for('auth.verify_email', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False

def send_welcome_email(user):
    msg = Message('Welcome to FinSight!',
                  recipients=[user.email])
    msg.body = f'''Welcome to FinSight, {user.full_name.split()[0]}!

We are thrilled to have you onboard. FinSight is designed to give you intelligent analytics for your financial future. 

Get started by adding your income sources, budgets, and expenses to your dashboard!

Happy Tracking,
The FinSight Team
'''
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

@auth.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            full_name=form.full_name.data,
            email=form.email.data.lower(),
            password_hash=hashed_password,
            is_verified=True
        )
        db.session.add(user)
        db.session.commit()
        
        # Optionally send a welcome email if you want, but skipping it to avoid SMTP errors on local test
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

@auth.route("/verify_email/<token>")
def verify_email(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    user_data = User.verify_registration_token(token)
    if user_data is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.register'))
    
    user = User.query.filter_by(email=user_data['email']).first()
    if not user:
        user = User(full_name=user_data['full_name'], email=user_data['email'], 
                    password_hash=user_data['password_hash'], is_verified=True)
        db.session.add(user)
        db.session.commit()
        send_welcome_email(user)
        flash('Your account has been verified! Welcome to FinSight.', 'success')
    else:
        flash('Your account is already verified! You can log in.', 'info')
        
    return redirect(url_for('auth.login'))

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            if not user.is_verified:
                flash('Please verify your email before logging in. Check your inbox.', 'warning')
                return redirect(url_for('auth.login'))
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            if user and user.google_id:
                flash('It looks like you signed up with Google. Please use "Login with Google", or click "Forgot Password" below to set a manual password.', 'info')
            else:
                flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@auth.route('/login/google')
def login_google():
    redirect_uri = url_for('auth.authorize_google', _external=True)
    return oauth.google.authorize_redirect(redirect_uri, prompt='select_account')

@auth.route('/authorize/google')
def authorize_google():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if user_info:
        email = user_info.get('email')
        name = user_info.get('name')
        google_id = user_info.get('sub')
        picture = user_info.get('picture')
        
        user = User.query.filter_by(email=email).first()
        if not user:
            # Create a new user with random password since they use Google
            random_pw = secrets.token_hex(16)
            hashed_pw = bcrypt.generate_password_hash(random_pw).decode('utf-8')
            user = User(full_name=name, email=email, password_hash=hashed_pw, 
                        google_id=google_id, profile_pic=picture, is_verified=True)
            db.session.add(user)
            db.session.commit()
            send_welcome_email(user)
            flash('Account created successfully! Welcome to FinSight.', 'success')
        else:
            # Update existing user if needed
            if not user.google_id:
                user.google_id = google_id
            if not user.is_verified:
                user.is_verified = True
                send_welcome_email(user)
            db.session.commit()
            
        login_user(user)
        return redirect(url_for('main.dashboard'))
    flash('Google login failed.', 'danger')
    return redirect(url_for('auth.login'))

@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture_fn)
    
    # Save the file
    form_picture.save(picture_path)
    return picture_fn

@auth.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.profile_pic = picture_file
            
        current_user.full_name = form.full_name.data
        current_user.income_sources = form.income_sources.data
        current_user.financial_preferences = form.financial_preferences.data
        
        # Check if email is being changed and if it's already taken
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('That email is taken. Please choose a different one.', 'danger')
                return render_template('auth/profile.html', title='Profile', form=form)
        
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.email.data = current_user.email
        form.income_sources.data = current_user.income_sources
        form.financial_preferences.data = current_user.financial_preferences
    return render_template('auth/profile.html', title='Profile', form=form)

def send_reset_email(user):
    token = user.get_token()
    msg = Message('Password Reset Request',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

@auth.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_request.html', title='Reset Password', form=form)

@auth.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    user = User.verify_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password_hash = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_token.html', title='Reset Password', form=form)

@auth.route("/change_password", methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.google_id and form.old_password.data:
            if not bcrypt.check_password_hash(current_user.password_hash, form.old_password.data):
                flash('Incorrect current password.', 'danger')
                return redirect(url_for('auth.change_password'))
        elif not current_user.google_id and not form.old_password.data:
             flash('You must provide your current password.', 'danger')
             return redirect(url_for('auth.change_password'))
             
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        current_user.password_hash = hashed_password
        db.session.commit()
        flash('Your password has been successfully updated!', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/change_password.html', title='Change Password', form=form)
