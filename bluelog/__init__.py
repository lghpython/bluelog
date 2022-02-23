import os 
import logging
import click
import os 
from logging.handlers import SMTPHandler, RotatingFileHandler

from flask import Flask, render_template, request
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from flask_sqlalchemy import get_debug_queries

from bluelog.extensions import bootstrap, db, moment, ckeditor, mail, login_manager, csrf
from bluelog.blueprints.admin import admin_bp
from bluelog.blueprints.auth import auth_bp
from bluelog.blueprints.blog import blog_bp
from bluelog.models import Admin, Category, Post, Comment,Link
from bluelog.settings import config

basedir=os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def create_app(config_name=None):

    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')
        
    app = Flask('bluelog')
    app.config.from_object(config[config_name])

    register_logging(app)
    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_errors(app)
    register_shell_context(app)
    register_template_context(app)
    register_request_handlers(app)
    return app


def register_logging(app):
    """自定义邮件发送错误日志格式， 和文件上传日志格式"""
    class RequestFormatter(logging.Formatter):
        
        def format(self, record):
            record.url = request.url
            record.remote_addr = request.remote_addr
            return super(RequestFormatter, self).format(record)

    request_formatter = RequestFormatter(
        '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
        '%(levelname)s in %(module)s: %(message)s'
    )
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = RotatingFileHandler(os.path.join(basedir,'logs/bluelog.log'),maxBytes=10*1024*1024,backupCount=10)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    mail_handler = SMTPHandler(
        mailhost=app.config['MAIL_SERVER'],
        fromaddr=app.config['MAIL_USERNAME'],
        toaddrs=['ADMIN_EMAIL'],
        subject='Bluelog Application Error',
        credentials=(app.config['MAIL_USERNAME'],app.config['MAIL_PASSWORD'])
    )
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(request_formatter)
    if not app.debug:
        app.logger.addHandler(mail_handler)
        app.logger.addHandler(file_handler)

def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    moment.init_app(app)
    ckeditor.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

def register_blueprints(app):
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(blog_bp)

def register_shell_context(app):

    @app.shell_context_processor
    def make_shell_context():
        """将数据库模型， 导入上下文管理器"""
        return dict(db=db, Admin=Admin, Post=Post, Category=Category, Comment=Comment)

def register_template_context(app):
    @app.context_processor
    def make_template_comtext():
        admin = Admin.query.first()
        categories = Category.query.order_by(Category.name).all()
        links = Link.query.order_by(Link.name).all()
        if current_user.is_authenticated:
            unread_comments = Comment.query.filter_by(reviewed=False).count()
        else:
            unread_comments = None
        return dict(admin=admin, categories=categories,links=links, unread_comments=unread_comments)

def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='删除数据库重新创建')
    def init_db(drop):
        """初始化数据库"""
        if drop:
            click.confirm('该操作为删除数据库操作 是否继续?', abort=True)
            db.drop_all()
            click.echo('成功删除数据库')
        db.create_all()
        click.echo('初始化数据库成功')

    @app.cli.command()
    @click.option('--username',prompt=True, help="用于登录的用户名")
    @click.option('--password',prompt=True,hide_input=True, confirmation_prompt=True,help="用于登录额用户密码")
    def init(username, password):
        """新建账户"""
        click.echo('初始化数据库')
        db.create_all()

        admin = Admin.query.first()
        if admin is not None:
            click.echo('更新已存在的管理员账户')
            admin.username=username
            admin.set_password(password)
        else:
            click.echo('产生临时的管理员账户')
            admin = Admin(username=username,blog_title='Blulog',blog_sub_title='real thing', name='Admin',about='关于我')
            admin.set_password(password)
            db.session.add(admin)

        category = Category.query.first()
        if category is None:
            click.echo('设置默认分类')
            category = Category(name='Default')
            db.session.add(category)
        db.session.commit()
        click.echo('初始化完成')

    @app.cli.command()
    @click.option('--category', default=10, help='生成分类默认 10个.')
    @click.option('--post', default=50, help='生成文章默认 50.')
    @click.option('--comment', default=500, help=' 生成评论默认 500.')
    def forge(category, post, comment):
        """生成虚拟数据"""
        from bluelog.fakes import fake_admin, fake_categories, fake_posts, fake_comments, fake_links

        db.drop_all()
        db.create_all()

        click.echo('生成管理员')
        fake_admin()

        click.echo('生成%d 个分类..' % category)
        fake_categories(category)

        click.echo('生成 %d 篇文章...' % post)
        fake_posts(post)

        click.echo('生成 %d 个评论...' % comment)
        fake_comments(comment)

        click.echo('生成随机链接 ')
        fake_links()

        click.echo('虚拟数据已生成.')

def register_errors(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_serve_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/404.html',description=e.description), 400          

def register_request_handlers(app):
    pass
    @app.after_request
    def query_profiler(response):
        for q in get_debug_queries():
            """  结束请求后, 调用方法查询数据库查询的语句中是否有查询时间大于设定的最慢门槛"""
            if q.duration >= app.config['BLUELOG_SLOW_QUERY_THRESHOLD']:
                app.logger.warning(
                    'Slow query: Duration: %f\n Context: %s\n Query: %s\n'
                    %(q.duration, q.context, q.statement)
                )

        return response
