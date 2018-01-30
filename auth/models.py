import datetime
import random

import flask
import flask_login
import flask_mail
import flask_wtf
import wtforms
import boto3

import dynamoDB
import GroceryDB

dynamodb = boto3.resource('dynamodb',region_name='us-east-2')
tables={
        'Users':dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Users','ID', GroceryDB.GroceryUser),
       }
mail = flask_mail.Mail()

class UserForm(flask_wtf.FlaskForm):
    usphone = '^[1]?[\-]?[\( ]?[0-9]{3}[\)]?[\-]?[0-9]{3}[\-]?[0-9]{4}$'
    uszipcode = '^[0-9]{5}(-[0-9]{4})?$'
    Email = wtforms.StringField('Email', validators=[wtforms.validators.DataRequired(),
                                                     wtforms.validators.Email()])
    Phone = wtforms.StringField('Phone', validators=[wtforms.validators.DataRequired(),
                                                                 wtforms.validators.Regexp(usphone)])
    FirstName = wtforms.StringField('FirstName', validators=[wtforms.validators.DataRequired()])
    LastName = wtforms.StringField('LastName', validators=[wtforms.validators.DataRequired()])
    Street = wtforms.StringField('Street', validators=[wtforms.validators.DataRequired()])
    Town = wtforms.StringField('Town', validators=[wtforms.validators.DataRequired()])
    State = wtforms.StringField('State', validators=[wtforms.validators.DataRequired()])
    Zipcode = wtforms.StringField('Zipcode', validators=[wtforms.validators.DataRequired(),
                                                                 wtforms.validators.Regexp(uszipcode)])
    Country = wtforms.SelectField('Country', validators=[wtforms.validators.DataRequired()],
                                                  id='United States of America')
    BirthDate = wtforms.DateField('BirthDate', validators=[wtforms.validators.DataRequired()],
                                                      format='%m/%d/%Y')
    Password = wtforms.PasswordField('Password', validators=[wtforms.validators.DataRequired(),
                                                                                 wtforms.validators.EqualTo('ConfirmPassword')])
    ConfirmPassword = wtforms.PasswordField('Confirm Password')
    SecretQuestion = wtforms.SelectField('SecretQuestion', validators=[wtforms.validators.DataRequired()],
                                              id="What is you mother's maiden name?")
    SecretAnswer = wtforms.StringField('SecretAnswer', validators=[wtforms.validators.DataRequired()])
    Submit = wtforms.SubmitField('Register')

    def validate_email(self, field):
                #raise ValidationError if already in use
        pass

class LoginForm(flask_wtf.FlaskForm):
    """Form for users to login"""
    Email = wtforms.StringField('Email', validators=[wtforms.validators.DataRequired(),
                                                     wtforms.validators.Email()])
    Password = wtforms.PasswordField('Password', validators=[wtforms.validators.DataRequired()])
    Submit = wtforms.SubmitField('Login')

class ConfirmEmailForm(flask_wtf.FlaskForm):
    """Form for users to login"""
    Email = wtforms.StringField('Email', validators=[wtforms.validators.DataRequired(),
                                                     wtforms.validators.Email()])
    PhoneCode = wtforms.StringField('PhoneCode', validators=[wtforms.validators.DataRequired()])
    EmailCode = wtforms.StringField('EmailCode', validators=[wtforms.validators.DataRequired()])
    Submit = wtforms.SubmitField('Login')

def getUser(email):
    print('getUser:',email)
    filter_expression = "Email = :e"
    projection_expression = "ID, Email"
    expression_attribute_values = {':e': email}
    #expression_attribute_names = {"#Lo": "Location", }
    user_proj = tables['Users'].scan(filter_expression, expression_attribute_values, 
                                   projection_expression)
    print('getUser Result:',user_proj)
    try:
        user=tables['Users'].get(user_proj[0]['ID'])
        print('getUser user:',user)
    except KeyError as e:
        return(None)
    except IndexError as e:
        return(None)
    return(user)

def userCodesMatch(user,emailcode,phonecode):
    if user and 'PhoneCode' in user.__data__ and 'EmailCode' in user.__data__ and 'CodeExpires' in user.__data__:
        #TODO check that CodeExpires is still valid
        if user.__data__['PhoneCode']==phonecode and user.__data__['EmailCode']==emailcode:
            #TODO delete phonecode and emailcode and CodeExpires, 
            user.__data__['PhoneCode'] = None
            user.__data__['EmailCode'] = None
            user.__data__['CodeExpires'] = None
            user.__data__['PhoneActive'] = str(datetime.datetime.now())
            user.__data__['EmailActive'] = str(datetime.datetime.now())
            user.save(overwrite=True)
            return(True)
    else:
        #TODO only allow three tries or else delete user and they need to reregister
        return(False)

auth = flask.Blueprint('auth', __name__)
mail = flask_mail.Mail()

@auth.route('/register', methods=['GET', 'POST'])
def register_user():
    """
    Handle requests to the /register route
    Add a user to the database through the registration form
    """
    form = UserForm()
    form.Country.choices = [('United States of America','United States of America'),('Canada','Canada')]
    form.SecretQuestion.choices = [(i,i) for i in ["What is your mother's maiden name?",
                                                           "What was the name of your first pet?"]]
    if flask.request.method=='POST' and form.validate_on_submit():
        print("Attempt to register user to Users Tables...")
        existing_user = getUser(form.Email.data)
        if existing_user:
            flask.flah("This user already exists.")
            return(flask.render_template('auth/register.html', form=form, title="Register"))
        #usertable = dynamodb.Table('GroceryFlaskApp-WebEnv-Users')
        usertable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Users','ID',GroceryDB.GroceryItem)
        #print(usertable) #TODO I DO NOT WANT TO CREATE TABLE HERE, rewrite to allow dynamodb.Table()
        usertable.hash_key='ID'
        flask.flash("%s %s being created"%(form.FirstName.data,form.LastName.data))
        user = GroceryDB.GroceryUser.fromValues(
            table = usertable,
            Email = form.Email.data,
            Phone = form.Phone.data,
            FirstName = form.FirstName.data,
            LastName = form.LastName.data,
            Street = form.Street.data,
            Town = form.Town.data,
            State = form.State.data,
            Zipcode = form.Zipcode.data,
            Country = form.Country.data,
            BirthDate = form.BirthDate.data.strftime("%d/%m/%Y"),
            Password = form.Password.data,
            SecretQuestion = form.SecretQuestion.data,
            SecretAnswer = form.SecretAnswer.data,
        )
        EmailCode = str(random.randint(1,999999))
        user.__data__['EmailCode'] = EmailCode
        PhoneCode = str(random.randint(1,9999))
        user.__data__['PhoneCode'] = PhoneCode
        user.__data__['CodeExpires'] = str(datetime.datetime.now()+datetime.timedelta(days=1))
        #This should be a new user so do not overwrite
        user.save(overwrite=False)
        #Send Email Code
        msg = flask_mail.Message("Hello",
                #sender="from@example.com",
                sender=("Flask App","nathan_walsh@verizon.net"),
                recipients=[form.Email.data])
        msg.body = "To confirm registration please follow this link: http://192.168.1.38:5001/confirm_email?emailcode="+EmailCode+"&email=nwalsh@alumni.brown.edu"
        mail.send(msg)
        #Send Phone Code
        client = boto3.client(
                'sns',
                region_name="us-east-1",
                )
        response = client.publish(
                PhoneNumber='+1'+form.Phone.data,
                Message='Your Grocery Flask verification code is %s.'%user.__data__['PhoneCode'],
                )
        print(response)
        flask.flash("Step 1 of registration complete.  You should get a text (SNS) message with a PIN.  You should also get an email with a link. Follow the link and type in the PIN to complete registration.")
        #redirect to the login page
        return(flask.redirect(flask.url_for('auth.login')))
    #load the registration template
    return(flask.render_template('auth/register.html', form=form, title='Register'))

@auth.route('/confirm_email', methods=['GET','POST'])
def confirm_email():
    form = ConfirmEmailForm()
    if 'emailcode' in flask.request.args:
        form.EmailCode.data = str(flask.request.args['emailcode'])
    if 'email' in flask.request.args:
        form.Email.data = flask.request.args['email']
    print(flask.request.args)

    if flask.request.method=='POST' and form.validate_on_submit():
        existing_user = getUser(form.Email.data)
        if existing_user and userCodesMatch(existing_user, form.EmailCode.data, form.PhoneCode.data):
            return(flask.redirect(flask.url_for('auth.login')))
        flask.flash("Codes do not match")
    return(flask.render_template('auth/confirm_email.html', form=form, title='Register'))

@auth.route('/login', methods=['GET','POST'])
def login():
    """
    Handle requests to the /login route
    Log a user in through the login form
    """
    form = LoginForm()
    if form.validate_on_submit():
        #check if user and password match dataase
        user = getUser(form.Email.data)
        print(user)
        if user is not None and user.verify_password(form.Password.data):
            # log employee in
            flask_login.login_user(user)
            #TODO: to prevent malicious sites and users we must evaluate 'next' to make sure it is a safe url
            next = flask.request.args.get('next')
            #if not is_safe_url(next):
            #    return(flask.abort(400))
            return(flask.redirect(next or flask.url_for('home_list')))
            #   return(flask.redirect(url_for('home')))
        else:
            flask.flash('Invalid email or password')
    return(flask.render_template('auth/login.html',form=form, title='Login'))



@auth.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return(flask.redirect(flask.url_for("home")))

