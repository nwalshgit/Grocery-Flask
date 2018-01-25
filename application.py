import boto3
import json
import decimal

import flask
import flask_wtf
import wtforms
from flask_login import current_user, login_required, LoginManager, login_user

import dynamoDB
import GroceryDB

dynamodb = boto3.resource('dynamodb',region_name='us-east-2')
tables = {'Items':dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Items','ID', GroceryDB.GroceryItem),
          'Groups':dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Groups','ID', GroceryDB.GroceryGroup),
          'Users':dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Users','ID', GroceryDB.GroceryUser),
          'Areas':dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Areas','ID', GroceryDB.GroceryArea),
         }

#class ItemForm(wtforms.Form): #This will clear your form each time, unless you initialize it
class ItemForm(flask_wtf.FlaskForm):
    #UserGroup = wtforms.HiddenField('UserGroup')
    #user_name = wtforms.HiddenField('user_name')
    uscurrency='^[\$]?[0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?$'
    usdecimal='^[0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]+)?$'
    Name = wtforms.StringField('Name', validators=[wtforms.validators.DataRequired()])
    #PkgPrice = wtforms.StringField('PkgPrice', validators=[wtforms.validators.Regexp(uscurrency)])
    PkgPrice = wtforms.DecimalField('PkgPrice', places=2)
    Size = wtforms.DecimalField('Size', places=4)
    Unit = wtforms.SelectField('Unit', validators=[wtforms.validators.DataRequired()], id="")
    Locations = wtforms.SelectMultipleField('Locations', validators=[wtforms.validators.DataRequired()],default=[])
    ItemGroup = wtforms.StringField('ItemGroup', validators=[wtforms.validators.DataRequired()])
    Manufacturer = wtforms.StringField('Manufacturer', validators=[wtforms.validators.DataRequired()])
    Taxable = wtforms.BooleanField('Taxable', validators=[wtforms.validators.Optional()])
    ItemStatus = wtforms.SelectField('ItemStatus', validators=[wtforms.validators.Optional()], id="")
    Home = wtforms.BooleanField('Home', validators=[wtforms.validators.Optional()])
    Barcode = wtforms.StringField('Barcode', validators=[wtforms.validators.DataRequired()])
    ListDate = wtforms.StringField('ListDate', validators=[wtforms.validators.Optional()])
    #TODO make sure it is a valid list if chosen
    Fees = wtforms.StringField('Fees', validators=[wtforms.validators.Optional()])
    #Recaptcha = flask_wtf.RecaptchaField()
    Submit = wtforms.SubmitField('Create')

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
    return(user)
    

def getLocationsJSON(UserGroup):
    ''' [{"ID":"xxx","Building":"xxx","Bay":"xxx"},] '''
    filter_expression = "UserGroup = :g"
    projection_expression = "ID, Building, Bay, SortOrder"
    expression_attribute_values = {':g': UserGroup}
    #expression_attribute_names = {"#Lo": "Location", }
    locations = tables['Areas'].scan(filter_expression, expression_attribute_values, 
                       projection_expression)
    #print("getLocationDict:",locations)
    return(locations)

def getLocationsDict(UserGroup):
    '''{"ID":"Location - Area",} '''
    location_dict = {}
    locations=getLocationsJSON(UserGroup)
    for location in locations: #TODO sort by Building and then Order
        location_dict[location['ID']] = {'Building': location['Building'],
                                         'Bay': location['Bay'],
                                         'SortOrder': location['SortOrder']}
    #print("getLocationDict:",location_dict)
    return(location_dict)

def getLocationsJSONSorted(UserGroup):
    locations=[]
    locationJSON=getLocationsJSON(UserGroup)
    for item in sorted(locationJSON, key=lambda item: (item['Building'], item['SortOrder'], item['ID'])):
        #if 'Items' not in value: value['Items']=[]
        #locations.append(["%s - %s"%(value['Building'],value['Bay']),value['Items']])
        locations.append(item)
    return(locations)


def getItemGroupsJSON(UserGroup):
    table=tables['Items']
    filter_expression = "UserGroup = :g and NOT (ItemStatus = :s)"
    #expression_attribute_names = {"#Gr": "Group", }
    projection_expression = "ItemGroup, Locations, Taxable, ItemStatus"
    expression_attribute_values = {':g': UserGroup, ':s': 'Discontinued'}
    items = table.scan(filter_expression, expression_attribute_values,
                       projection_expression)
    return(items)

def getItemGroupsByLocation(UserGroup):
    items=getItemGroupsJSON(UserGroup)
    #print("items:",items)
    locations=getLocationsDict(UserGroup)
    #print("locations:",locations)
    for item in items:
        for location in item['Locations']:
            #if location not in locations:  #TODO this should never happen, check that it doesnt 
            #    locations[location]={}
            if location not in locations: #TODO we should never get here
                print("DB inconsistency. location %s does not exist"%location)
                continue
            if 'Items' not in locations[location]:
                locations[location]['Items']={}
            if 'ItemStatus' not in item:
                item['ItemStatus']=''
            if item['ItemGroup'] not in locations[location]['Items']:
                locations[location]['Items'][item['ItemGroup']]={}
                locations[location]['Items'][item['ItemGroup']]['ItemStatus']=''
            #print(locations[location]['Items'][item['ItemGroup']])
            if item['ItemStatus']=='Needed' or \
               locations[location]['Items'][item['ItemGroup']]['ItemStatus']=='Needed':
                    locations[location]['Items'][item['ItemGroup']]['ItemStatus']='Needed'
            elif item['ItemStatus']=='Discontinued' or \
               locations[location]['Items'][item['ItemGroup']]['ItemStatus']=='Discontinued':
                    locations[location]['Items'][item['ItemGroup']]['ItemStatus']='Discontinued'
    return(locations);

def getItemGroupsBySortedLocation(UserGroup):
    locations=[]
    locationJSON=getItemGroupsByLocation(UserGroup)
    for key,value in sorted(locationJSON.items(), key=lambda item: (item[1]['Building'], item[1]['SortOrder'], item[0])):
        if 'Items' not in value: value['Items']=[]
        locations.append(["%s - %s"%(value['Building'],value['Bay']),value['Items']])
    return(locations)

def makeFirstList(Group='nwalsh'):
    items = getItemCollections(Group)
    for item in items:
        GroceryDB.GroceryList(tables['List'],Group,'0',item).save()

# EB looks for an 'application' callable by default.
application = flask.Flask(__name__)
#csrf.init_app(application)
#CSRF needs a secret key defined in the environment for it to work
application.config.update(dict(
    SECRET_KEY = "GroceryApp-WebEnv-fha7f1e4g",
    WTF_CSRF_SECRET_KEY = 'CSRF-fha7fle4g'
))
#hook to allow flask_login to talk with application
login_manager = LoginManager()
login_manager.init_app(application)

@application.route('/', methods=['GET'])
def home():
    """add a rule for the index page."""
    return(flask.render_template('home/home.html',title='Home', current_user=current_user))

@application.route('/planning', methods=['GET'])
@login_required
def home_list():
    """list all of the itemcollections in home, grouped and sorted by area""" 
    UserGroup='nwalsh'
    #current_user='nwalsh'
    return(flask.render_template('home/items.html',title='Planning', 
                           #current_user=current_user, 
                           UserGroup=UserGroup,
                           itemcollections=getItemGroupsBySortedLocation(UserGroup)))

@application.route('/item', methods=['GET','POST'])
@login_required
def add_item():
    """Asks for form for new item, Saves new item from form"""
    UserGroup='nwalsh'
    #current_user='nwalsh'
    #print("add_item: Locations=",getLocationsJSONSorted(UserGroup))
    form=ItemForm()
    form.ItemStatus.choices = [('','Select a status...')]+[(value,value) for value in GroceryDB.ITEMSTATUS]
    form.Unit.choices = [('','Select a unit...')]+[(value,value) for value in GroceryDB.UNITS]
    form.Locations.choices = [(loc['ID'],loc['Building']+" - "+loc['Bay']) for loc in getLocationsJSONSorted(UserGroup)]
    #form.unit.choices = [(unit,unit) for unit in Unit.query.all()]
    flask.flash("validation: "+str(form.validate_on_submit()))
    print(form.data)
    if flask.request.method =="POST" and form.validate_on_submit():
        print("Attempt to save item to Items Tables...")
        itemtable = dynamodb.Table('GroceryFlaskApp-WebEnv-Items')
        print(itemtable)
        itemtable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Items','ID',GroceryDB.GroceryItem)
        print(itemtable) #TODO I DO NOT WANT TO CREATE TABLE HERE, rewrite to allow dynamodb.Table()
        itemtable.hash_key='ID'
        flask.flash("'"+form.Name.data+"' being created")
        item=GroceryDB.GroceryItem.fromValues(
                itemtable,UserGroup,
                form.Name.data,
                decimal.Decimal(form.PkgPrice.data),
                decimal.Decimal(form.Size.data),
                form.Unit.data,
                form.Locations.data,
                form.ItemGroup.data,
                form.Manufacturer.data,
                form.Taxable.data,
                form.ItemStatus.data,
                form.ListDate.data,
                form.Home.data,
                form.Barcode.data,
                form.Fees.data)
        item.save()
        return(flask.redirect(flask.url_for('home_list')))
    return(flask.render_template('home/item.html',title='New Item',
                           #current_user=current_user, 
                           UserGroup=UserGroup,
                           form=form
                           ))

@application.route('/register', methods=['GET', 'POST'])
def register_user():
    """
    Handle requests to the /register route
    Add a user to the database through the registration form
    """
    form = UserForm()
    form.Country.choices = [('United States of America','United States of America'),('Canada','Canada')]
    form.SecretQuestion.choices = [(i,i) for i in ["What is your mother's maiden name?",
                                                   "What was the name of your first pet?"]]
    #current_user='Guest'
    if flask.request.method=='POST' and form.validate_on_submit():
        print("Attempt to register user to Users Tables...")
        usertable = dynamodb.Table('GroceryFlaskApp-WebEnv-Users')
        print(usertable)
        usertable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Users','ID',GroceryDB.GroceryItem)
        print(usertable) #TODO I DO NOT WANT TO CREATE TABLE HERE, rewrite to allow dynamodb.Table()
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
        #This should be a new user so do not overwrite
        user.save(overwrite=False)
        flask.flash("Step 1 of registration complete.  You should get a text (SNS) message with a PIN.  You should also get an email with a link.  Follow the link and type in the PIN to complete registration.")
        #redirect to the login page
        return(flask.redirect(flask.url_for('login')))
    #load the registration template
    return(flask.render_template('home/user.html', form=form, title='Register'))

@application.route('/login', methods=['GET','POST'])
def login():
    """
    Handle requests to the /login route
    Log a user in through the login form
    """
    form = LoginForm()
    if form.validate_on_submit():
        #check if user and password match dataase
        flask.flash('TODO: finish password verification')
        user = getUser(form.Email.data)
        print(user)
        if user is not None and user.verify_password(form.Password.data):
        #LIKE GROCERY0
        #employee = Employee.query.filter_by(email=form.email.data).first()
        #if employee is not None and employee.verify_password(
        #        form.password.data):
        #LIKE CODE EXAMPLE
        #employee = database.get(form.Email.data)
        #if employee and employee.verify_password(form.Password.data):
            # log employee in
            login_user(user)
        #   return(flask.redirect(url_for('home')))
        #else:
        #   flask.flash('Invalid email or password')

        #TODO: to prevent malicious sites and users we must evaluate 'next' to make sure it is a safe url
        next = flask.request.args.get('next')
        #if not is_safe_url(next):
        #    return(flask.abort(400))
        return(flask.redirect(next or flask.url_for('home_list')))
    return(flask.render_template('home/login.html',form=form, title='Login'))

#TODO define /logout


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run(host='0.0.0.0',port=5001)

