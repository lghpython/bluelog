import random
from faker import Faker
from bluelog.extensions import db
from sqlalchemy.exc import IntegrityError
from bluelog.models import Admin, Category, Post, Comment,Link

fake = Faker()

def fake_admin():
    admin = Admin(
        username='admin',
        blog_title='Bluelog',
        blog_sub_title="No, I'm the real thing. ",
        name='light',
        about='Um, xxxxxxxxxxxx'

    )
    admin.set_password('helloflask')
    db.session.add(admin)
    db.session.commit()


def fake_categories(count=10):
    category = Category(name='Default')
    db.session.add(category)
    for i in range(count):
        category = Category(name=fake.word())
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_posts(count=50):
    for i in range(count):
        post = Post(
            title=fake.sentence(),
            body=fake.text(2000),
            category=Category.query.get(random.randint(1, Category.query.count())),
            timestamp=fake.date_time_this_year()
        )
        db.session.add(post)
    db.session.commit()


def fake_comments(count=500):
    for i in range(count):
        comment = Comment(
            author =fake.name(),
            email = fake.email(),
            site = fake.url(),
            body = fake.sentence(),
            timestamp=fake.date_time_this_year(),
            reviewed = True,
            post=Post.query.get(random.randint(1, Post.query.count()))
        )
        db.session.add(comment)

    salt = int(count*0.1)
    for i in range(salt):
        # 未审核的评论
        comment = Comment(
            author =fake.name(),
            email = fake.email(),
            site = fake.url(),
            body = fake.sentence(),
            timestamp=fake.date_time_this_year(),
            reviewed = False,
            post=Post.query.get(random.randint(1, Post.query.count()))
        )
        db.session.add(comment)

        # from_admin=True
        comment = Comment(
            author =fake.name(),
            email = fake.email(),
            site = fake.url(),
            body = fake.sentence(),
            timestamp=fake.date_time_this_year(),
            reviewed = True,
            from_admin=True,
            post=Post.query.get(random.randint(1, Post.query.count()))
        )
        db.session.add(comment)
    db.session.commit()

    # replies
    for i in range(salt):
        comment = Comment(
            author =fake.name(),
            email = fake.email(),
            site = fake.url(),
            body = fake.sentence(),
            timestamp=fake.date_time_this_year(),
            reviewed = True,
            replied = comment.query.get(random.randint(1,Comment.query.count())),
            post=Post.query.get(random.randint(1, Post.query.count()))
        )
        db.session.add(comment)


def fake_links():
    twitter = Link(name='Twitter', url="#")
    facebook = Link(name='Facebook', url="#")
    linkedin = Link(name='LinkedIn', url="#")
    google = Link(name='Google', url="#")
    baidu = Link(name='百度', url="#")
    db.session.add_all([twitter,facebook,linkedin, google, baidu])
    db.session.commit()