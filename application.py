import boto3
import json
import decimal

import flask
import flask_wtf
import wtforms

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


@application.route('/', methods=['GET'])
def home():
    """add a rule for the index page."""
    return(flask.render_template('home/home.html',title='Home', current_user=current_user))

# add a rule when the page is accessed with a location appended to the site
# URL.
#application.add_url_rule('/<location>', 'hello', (lambda location:
#    header_text + say_hello(location) + home_link + footer_text))

@application.route('/planning', methods=['GET'])
def list_itemcollections_home():
    """list all of the itemcollections in home, grouped and sorted by area""" 
    UserGroup='nwalsh'
    current_user='nwalsh'
    return(flask.render_template('home/items.html',title='Planning', 
                           current_user=current_user, UserGroup=UserGroup,
                           itemcollections=getItemGroupsBySortedLocation(UserGroup)))

@application.route('/item', methods=['GET','POST'])
def add_item():
    """Asks for form for new item, Saves new item from form"""
    UserGroup='nwalsh'
    current_user='nwalsh'
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
        print(itemtable)
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
        return(flask.redirect(flask.url_for('list_itemcollections_home')))
    return(flask.render_template('home/item.html',title='New Item',
                           current_user=current_user, UserGroup=UserGroup,
                           form=form
                           ))

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run(host='0.0.0.0',port=5001)
