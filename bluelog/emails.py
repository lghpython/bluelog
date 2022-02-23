from threading import Thread
from flask import url_for, current_app
from flask_mail import Message

from bluelog.extensions import mail

def _send_async_mail(app, message):
    with app.app_context():
        mail.send(message)


def send_mail(subject, to, html):
    app = current_app._get_current_object()
    message = Message(subject, recipients=[to], html=html)
    thr = Thread(target=_send_async_mail, args=[app, message])
    thr.start()
    return thr

def  send_new_comment_mail(post):
    post_url = url_for('blog.show_post', post_id=post.id, _external=True)+ '#comments'
    send_mail(subject='新评论', to=current_app.config['BLUELOG_EMAIL'],\
        html='<p>你的文章有新的一条评论 <i>%s</i>, 点击下方查看:</p>'
                '<p><a href="%s">%s</a></P>'
                '<p><small style="color: #868e96">请不要回复该邮件.</small></p>'
                % (post.title, post_url, post_url))


def  send_new_reply_email(comment):
    post_url = url_for('blog.show_post', post_id=comment.post_id, _external=True )+"#comment"
    send_mail(subject='新回复', to=current_app.config['BLUELOG_EMAIL'],\
        html='<p>你的评论有新的一条回复 <i>%s</i>, 点击下方查看:</p>'
                '<p><a href="%s">%s</a></P>'
                '<p><small style="color: #868e96">请不要回复该邮件.</small></p>'
                % (comment.post.title, post_url, post_url))