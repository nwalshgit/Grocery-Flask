import boto3, json
from flask import Flask, render_template
import dynamoDB, GroceryDB

dynamodb = boto3.resource('dynamodb',region_name='us-east-2')
tables = {'Items':dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Items','ID', GroceryDB.GroceryItem),
          'Groups':dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Groups','ID', GroceryDB.GroceryGroup),
          'Users':dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Users','ID', GroceryDB.GroceryUser),
          'Areas':dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Areas','ID', GroceryDB.GroceryArea),
         }

def itemsToLocationDict(items):
    locationdict={}
    for item in items:
        for location in item['Locations']:
            if location not in locationdict: 
                locationdict[location]={}
            locationdict[location][item['ItemGroup']]=True
    return(locationdict);


def getItemCollections(Group='nwalsh'):
    table=tables['Items']
    filter_expression = "UserGroup = :g"
    #expression_attribute_names = {"#Gr": "Group", }
    projection_expression = "ItemGroup, Locations, Taxable, Needed"
    expression_attribute_values = {':g': 'nwalsh'}
    items = table.scan(filter_expression, expression_attribute_values,
                       projection_expression)
    return(items)

def makeFirstList(Group='nwalsh'):
    items = getItemCollections(Group)
    for item in items:
        GroceryDB.GroceryList(tables['List'],Group,'0',item).save()

# print a nice greeting.
def say_hello(username = "World"):
    return(str(itemsToLocationDict(getItemCollections()))+'<p>Hello %s!</p>\n' % username)

# some bits of text for the page.
header_text = '''
    <html>\n<head> <title>Grocery List</title> </head>\n<body>'''
instructions = '''
    <p><em>Hint</em>: This is a RESTful web service! Append a location
    to the URL (for example: <code>/BJs</code>) to GET details of that 
    location.</p>\n'''
home_link = '<p><a href="/">Back</a></p>\n'
footer_text = '</body>\n</html>'

# EB looks for an 'application' callable by default.
application = Flask(__name__)

# add a rule for the index page.
application.add_url_rule('/', 'index', (lambda: header_text +
    say_hello() + instructions + footer_text))

# add a rule when the page is accessed with a location appended to the site
# URL.
#application.add_url_rule('/<location>', 'hello', (lambda location:
#    header_text + say_hello(location) + home_link + footer_text))

@application.route('/planning', methods=['GET'])
def list_itemcollections_home():
    """list all of the itemcollections in home, grouped and sorted by area""" 
    #TODO GroceryItem is missing locations
    current_user='nwalsh'
    itemcollections=[{'name':'Home - Fridge',  
                      'items':[{'name':'Strawberries','needed':True},
                               {'name':'Turkey, sliced','needed':False}]},
                      {'name':'Home - Cabinets',
                       'items':[{'name':'','needed':False}]},
                    ]
    return(render_template('home/items.html',title='Planning', current_user=current_user,
                           itemcollections=itemcollections))

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run(port=5001)

