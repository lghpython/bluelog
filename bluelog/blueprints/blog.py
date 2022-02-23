from crypt import methods
from flask import flash, Blueprint, render_template, current_app, request, url_for, flash,redirect, abort, make_response
from flask_login import login_required, current_user

from bluelog.forms import AdminCommentForm, PostForm, CommentForm
from bluelog.models import Post, Comment, Category
from bluelog.extensions import db
from bluelog.emails import send_new_reply_email, send_new_comment_mail
from bluelog.utils import redirect_back

  
blog_bp = Blueprint('blog', __name__,)


@blog_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, \
        per_page=current_app.config['BLUELOG_POST_PER_PAGE'])
    posts = pagination.items
    return render_template('blog/index.html', pagination=pagination, posts=posts)


@blog_bp.route('/about')
def about():
    """ 博客首页 """
    return render_template('blog/about.html')


@blog_bp.route('/show_category/<int:category_id>')
def show_category(category_id):
    """ 显示分类 """
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_POST_PER_PAGE']
    pagination = Post.query.with_parent(category).order_by(Post.timestamp.desc()).paginate(page,per_page)
    posts = pagination.items
    return render_template('blog/category.html', pagination=pagination, posts=posts, category=category)


@blog_bp.route('/show_post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    """  显示文章 """
    post = Post.query.get_or_404(post_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(post).filter_by(reviewed=True).paginate(page,per_page)
    comments = pagination.items

    if current_user.is_authenticated:
        form = AdminCommentForm()
        form.author.data = current_user.name
        form.email.data = current_app.config['BLUELOG_EMAIL']
        form.site.data = url_for('.index')
        from_admin = True
        reviewed = True
    else:
        form = CommentForm()
        from_admin = False
        reviewed = False
    
    if form.validate_on_submit():
        comment = Comment(
            author = form.author.data,
            email = form.author.data,
            site = form.site.data,
            from_admin=from_admin,
            reviewed = reviewed
        )
        
        reply_id = request.args.get('reply')
        if reply_id:
            replied_comment = Comment.query.get_or_404(reply_id)
            comment.replied = replied_comment
            # 发送邮件
            send_new_reply_email(replied_comment)
        db.session.add(comment)
        db.session.commit()
        if current_user.is_authenticated:  # send message based on authentication status
            flash('评论发表成功.', 'success')
        else:
            flash('感谢 你的评论将在审核后发表.', 'info')
            send_new_comment_mail(post)  # 发送通知邮件给 admin
        return redirect(url_for('.show_post', post_id=post_id))

    return render_template('blog/post.html', post=post, pagination=pagination)    


@blog_bp.route('/reply/comment/<int:comment_id>')
def reply_comment(comment_id):
    """ 回复评论 """
    comment = Comment.query.get_or_404(comment_id)
    if not comment.post.can_comment:
        flash('评论功能未开启', 'warning')
        return redirect(url_for('.show_post', post_id=comment.post.id))
    return redirect(url_for('.show_post', post_id=comment.post.id, \
        reply=comment_id, author=comment.author)+'#comment-form')


@blog_bp.route('/change-theme/<theme_name>')
def change_theme(theme_name):
    """ 改变主题 """
    if theme_name not in current_app.config['BLUELOG_THEMES'].keys():
        abort(404)

    response = make_response(redirect_back())
    response.set_cookie('theme', theme_name, max_age=30*24*60*60)
    return response

    