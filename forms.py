from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, FloatField, BooleanField, FileField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    user_type = SelectField('User Type', choices=[('farmer', 'Farmer'), ('customer', 'Customer')])
    phone = StringField('Phone Number', validators=[Optional()])
    submit = SubmitField('Register')

class FarmerProfileForm(FlaskForm):
    farm_name = StringField('Farm Name', validators=[DataRequired()])
    farm_location = StringField('Farm Location', validators=[DataRequired()])
    farm_size = StringField('Farm Size', validators=[Optional()])
    growing_practices = TextAreaField('Growing Practices', validators=[Optional()])
    payment_info = StringField('Payment Information (UPI/Bank)', validators=[DataRequired()])
    bio = TextAreaField('About Your Farm', validators=[Optional()])
    profile_picture = FileField('Profile Picture', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save Profile')

class CustomerProfileForm(FlaskForm):
    delivery_address = TextAreaField('Delivery Address', validators=[DataRequired()])
    preferred_payment = SelectField('Preferred Payment Method', 
                                   choices=[('upi', 'UPI'), ('bank_transfer', 'Bank Transfer'), ('cash_on_delivery', 'Cash on Delivery')])
    profile_picture = FileField('Profile Picture', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save Profile')

class CropForm(FlaskForm):
    name = StringField('Crop Name', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('vegetables', 'Vegetables'), 
        ('fruits', 'Fruits'),
        ('grains', 'Grains'),
        ('herbs', 'Herbs'),
        ('other', 'Other')
    ])
    price = FloatField('Price', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    unit = SelectField('Unit', choices=[
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('piece', 'Piece'),
        ('bunch', 'Bunch'),
        ('lb', 'Pound')
    ])
    description = TextAreaField('Description', validators=[DataRequired()])
    harvest_date = DateField('Harvest Date', validators=[Optional()])
    images = FileField('Images', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    is_available = BooleanField('Available for Sale', default=True)
    submit = SubmitField('Save Crop')

class OrderStatusForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('rejected', 'Rejected')
    ])
    submit = SubmitField('Update Status')

class PaymentForm(FlaskForm):
    payment_screenshot = FileField('Payment Screenshot', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Confirm Payment')
