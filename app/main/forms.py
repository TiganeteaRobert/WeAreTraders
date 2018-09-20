from flask import request
from flask_wtf import FlaskForm
from flask_uploads import UploadSet, IMAGES
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, SelectField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import _, lazy_gettext as _l
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))


class PostForm(FlaskForm):
    title = TextAreaField(_l('Add a title to your listing.'), validators=[DataRequired()])
    post = TextAreaField(_l('Add a description.'), validators=[DataRequired()])
    price = IntegerField(_l('Add a price.'), validators=[DataRequired()])
    dropdown_list = [('electronics', 'Electronics'), ('clothes', 'Clothes') , ('pets', 'Pets')]
    category = SelectField('Listing Category', choices=dropdown_list, default=1)
    picture = FileField('Add a picture.', validators=[
        FileRequired(),
    ])
    submit = SubmitField(_l('Submit'))

class PostReviewForm(FlaskForm):
    title = TextAreaField(_l('Add a title to your review.'), validators=[DataRequired()])
    body = TextAreaField(_l('Write a review.'), validators=[DataRequired()])
    dropdown_list = [('1','1'), ('2','2'), ('3','3'), ('4','4'), ('5','5'), ('6','6'), ('7','7'), ('8','8'), ('9','9'), ('10','10')]
    rating = SelectField('Select a rating (1-10)', choices=dropdown_list, default=1)
    submit = SubmitField(_l('Submit'))

