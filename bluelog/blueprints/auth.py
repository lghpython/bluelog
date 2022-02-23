from flask import Blueprint, render_template, flash
from flask_login import current_user, login_user, logout_user, login_required

from bluelog.utils import redirect_back
from bluelog.models import Admin
from bluelog.forms import LoginForm


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return render_template('bluelog:index')

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data
        admin = Admin.query.first()
        if admin:
            if username == admin.username and admin.validate_password(password):
                login_user(admin, remember)
                flash('Welcome back', 'info')
                return redirect_back()
            flash('Invid username or password', ' warning')
        else:
            flash('No Account', 'warning')
    return render_template('auth/login.html', form=form )

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout success', 'info')
    return redirect_back()