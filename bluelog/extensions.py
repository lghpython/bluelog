from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_mail import Mail
from flask_ckeditor import CKEditor
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()
bootstrap = Bootstrap()
moment = Moment()
mail = Mail()
ckeditor = CKEditor()
login_manager = LoginManager()
csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id):
    """导入用户"""
    from bluelog.models import Admin
    user = Admin.query.get(int(user_id))
    return user


# 设置登入视图端点值和登入自定义信息 及登入信息分类
login_manager.login_view = 'auth.login'
login_manager.login_message =  u"请先登录"
login_manager.login_message_category = 'warning'