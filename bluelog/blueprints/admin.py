from flask import request, current_app, render_template, flash, redirect, url_for, Blueprint, send_from_directory
from flask_login import login_required, current_user
from flask_ckeditor import upload_success, upload_fail
from bluelog.models import Category, Post, Comment, Link
from bluelog.forms import PostForm, SettingForm, CategoryForm, LinkForm
from bluelog.extensions import db
from bluelog.utils import redirect_back, allowed_file

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingForm()
    if form.validate_on_submit():
        current_app.name = form.name.data
        current_app.blog_title = form.blog_title.data
        current_app.blog_sub_title = form.blog_sub_title.data
        current_app.about = form.about.data
        db.session.commit()
        flash('博客设置更新成功', 'info')
        return redirect(url_for('blog.index'))
    
    form.name.data = current_user.name
    form.blog_title.data = current_user.blog_title
    form.blog_sub_title.data = current_user.blog_sub_title
    form.about.data = current_user.about
    return render_template('admin/settings.html', form=form)



@admin_bp.route('/post/manage')
@login_required
def manage_post():
    page = request.args.get('page',1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page,\
        per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
    posts = pagination.items
    return render_template('admin/manage_post.html', pagination=pagination, posts=posts, page=page)


@admin_bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            body=form.body.data,
            category=Category.query.get(form.category.data)
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created', 'success')
        return redirect(url_for('blog.show_post', post_id=post.id))
    return render_template('admin/new_post.html', form=form)

@admin_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    form = PostForm()
    post = Post.query.get_or_404(post_id)
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        post.category = Category.query.get(form.category.data)
        db.session.commit()
        flash('Edit post success', 'success')
        return redirect(url_for('blog.show_post', post_id=post.id))
    form.title.data = post.title
    form.body.data = post.body
    form.category.data = post.category_id
    return render_template('admin/edit_post.html', form=form)


@admin_bp.route('/post/<int:post_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('文章删除成功', 'success')
    return redirect_back()


@admin_bp.route('/post/<int:post_id>/set_comment', methods=['POST'])
@login_required
def set_comment(post_id):
    post = Post.query.get_or_404(post_id)
    if post.can_comment:
        post.can_comment=False
        flash('文章取消评论成功', 'success')
    else:
        post.can_comment = True
        flash('文章开启评论成功', 'success')
    db.session.commit()
    return redirect_back()


@admin_bp.route('/post/manage_comment')
@login_required
def manage_comment():
    filter_rule= request.args.get('filter', 'all')
    page = request.args.get('page', 1,  type=int)
    per_page = current_app.config['BLUELOG_COMMENT_PER_PAGE']
    if filter_rule=='unread': # 审核过的评论排序
        filtered_comments = Comment.query.filter_by(reviewed=False)
    elif filter_rule=='admin': # 管理员评论排序
        filtered_comments=Comment.query.filter_by(from_admin=True)
    else:
        filtered_comments=Comment.query

    pagination =filtered_comments.order_by(Comment.timestamp.desc()).paginate(page, per_page)
    comments = pagination.items
    return render_template('admin/manage_comment.html', comments=comments, pagination=pagination)



@admin_bp.route('/comment/<int:comment_id>/approve', methods=['POST'])
@login_required
def approve_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.reviewed=True
    db.session.commit()
    flash('审核评论成功', 'success')
    return redirect_back()


@admin_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('删除评论成功', 'success')
    return redirect_back()

@admin_bp.route('/category/new', methods=['GET', 'POST'])
@login_required
def new_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category=Category(name=form.name.data)
        db.session.add(category)
        db.session.commit()
        flash('添加新分类成功', 'warning')
        return redirect(url_for('.manage_category'))
    return render_template('admin/new_category.html', form=form)


@admin_bp.route('/category/manage')
@login_required
def manage_category():
    return render_template('admin/manage_category.html')


@admin_bp.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    form=CategoryForm()
    category = Category.query.get_or_404(category_id)
    if category.id ==1:
        flash('无法修改默认分类', 'warning')
        return redirect(url_for('blog.index'))
    if form.validate_on_submit():
        category.name = form.name.data
        db.session.commit()
        flash('编辑分类成功', 'success')
        return redirect(url_for('.manage_category'))
    form.name.data = category.name
    return render_template('admin/edit_category.html', form=form)


@admin_bp.route('/category/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """删除分类"""
    print(11111)
    category = Category.query.get_or_404(category_id)
    print(category_id)
    if category.id==1:
        flash('不能删除默认分类', 'warning')
        return redirect(url_for('blog.index'))
    category.delete()
    flash('删除分类成功', 'success')
    return redirect(url_for('.manage_category'))


@admin_bp.route('/link/manage')
@login_required
def manage_link():
    return render_template('admin/manage_link.html')


@admin_bp.route('/link/new', methods=['GET', 'POST'])
@login_required
def new_link():
    form = LinkForm()
    if form.validate_on_submit():
        link = Link(
            name = form.name.data,
            url=form.url.data,
        )
        db.session.add(link)
        db.session.commit()
        flash('添加链接成功', 'success')
        return redirect(url_for('.manage_link'))
    return render_template('admin/new_link.html', form=form)


@admin_bp.route('/link/<int:link_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_link(link_id):
    form = LinkForm()
    link = Link.query.get_or_404(link_id)
    if form.validate_on_submit():
        link.name = form.name.data,
        link.url =form.url.data,
        db.session.commit()
        flash('更新链接成功', 'success')
        return redirect(url_for('.manage_link'))
    form.name.data = link.name
    form.url.data = link.url
    return render_template('admin/edit_link.html', form=form)


@admin_bp.route('/link/<int:link_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_link(link_id):
    link = Link.query.get_or_404(link_id)
    
    db.session.remove(link)
    db.session.commit()
    flash('删除链接成功', 'success')
    return redirect(url_for('.manage_link'))


@admin_bp.route('/uploads/<path:filename>')
def get_image(filename):
    return send_from_directory(current_app.cofig['BLUELOG_UPLOAD_PATH'])


@admin_bp.route('/uploads', methods=['POST'])
def upload_image():
    f = request.files.get('upload')
    if not allowed_file(f.filename):
        return upload_fail('只上传图片格式')
    f.save(os.path.join(current_app.config['BLUELOG_UPLOAD_PATH']))

    url = url_for('.get_image', filenaeme=f.filename)
    return upload_success(f.filename)