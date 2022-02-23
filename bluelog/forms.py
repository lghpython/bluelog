
from xml.dom import ValidationErr
from flask_wtf import FlaskForm 
from wtforms.validators import DataRequired, Length, Email, URL, Optional
from wtforms import \
    (StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, HiddenField, ValidationError)
from flask_ckeditor import CKEditorField
from bluelog.models import Category

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(1,128)])
    remember = BooleanField('remember me')
    submit = SubmitField('Log in ')

class  SettingForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1,30)])
    blog_title = StringField('Blog Title', validators=(DataRequired(), Length(1, 60)))
    blog_sub_title = StringField('Blog Sub Title', validators=[DataRequired(), Length(1,100)])
    about = CKEditorField('about page', validators=[DataRequired()])
    submit = SubmitField()

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1,30)])
    category = SelectField('Category', coerce=int, default=1)
    body = CKEditorField('Body', validators=[DataRequired()])
    submit = SubmitField()

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args,**kwargs)
        self.category.choices=[(category.id, category.name) \
            for category in Category.query.order_by(Category.name).all()]


class CommentForm(FlaskForm):
    author = StringField('Author', validators=[DataRequired(), Length(1, 30)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1,254) ])
    site =  StringField('Site', validators=[Optional(), URL(), Length(0,255)])
    body = TextAreaField('Comment', validators= [DataRequired()])
    submit = SubmitField()


class AdminCommentForm(FlaskForm):
    author = HiddenField()
    email = HiddenField()
    site = HiddenField()


class CategoryForm(FlaskForm):
    name = StringField('category', validators=[DataRequired(), Length(1, 30)])
    submit = SubmitField()

    def validate_name(self, field):
        if Category.query.filter_by(name=field.data).first():
            raise ValidationError('分类已存在')

class LinkForm(FlaskForm):
    name = StringField('Name',validators=[DataRequired(), Length(1, 30)])
    url = StringField('Link', validators=[DataRequired(), URL(), Length(1,255)] )
    submit = SubmitField()
