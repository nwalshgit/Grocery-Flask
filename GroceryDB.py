import decimal, uuid
import dynamoDB

UNITS={'mg':{},'g':{},'lb':{},'oz':{},'mL':{},'L':{},'gal':{},'floz':{},'ea':{},'dz':{},}

class GroceryItem(dynamoDB.DynamoItem):
    def validate(self,data):
        print("Groceryitem.validate",data)
        super().validate(data)
        assert('Group' in data and isinstance(data['Group'],str))
        assert('Name' in data and isinstance(data['Name'],str))
        assert('Manufacturer' in data and isinstance(data['Manufacturer'],str))
        assert('Size' in data)
        assert(isinstance(data['Size'],float) or isinstance(data['Size'],int) or isinstance(data['Size'],decimal.Decimal))
        assert('Unit' in data and data['Unit'] in UNITS)
        if 'CollectionGroup' in data:
            assert(isinstance(data['CollectionGroup'],str))
        if 'Taxable' in data:
            assert(isinstance(data['Taxable'],Boolean))
    def fromValues(table,Group,Barcode,Name,Manufacturer,Size,Unit,ItemCollection=None,Taxable=False):
        data = {'ID': str( uuid.uuid5(uuid.NAMESPACE_OID, "\t".join([Group,Name,Manufacturer,str(Size),Unit])) ),
                'Group': Group,
                'Name': Name,
                'Manufacturer': Manufacturer,
                'Size' : Size,
                'Unit' : Unit,
               }
        if Barcode: data['Barcode']=Barcode
        if ItemCollection: data['ItemCollection']=ItemCollection
        if Taxable: data['Taxable']=0.06125  #only define if it is taxable
        #print("fromValues",data)
        return(GroceryItem(table, data))
    def set(self,key,value):
        print("Setting",key,"to",value)
        assert(key not in ['ID','Group','Name','Manufacturer','Size','Unit'])
        super().set(key,value)

class GroceryArea(dynamoDB.DynamoItem):
    def validate(self,data):
        super().validate(data)
        assert('Group' in data and isinstance(data['Group'],str))
        assert('Location' in data and isinstance(data['Group'],str))
        assert('Name' in data and isinstance(data['Group'],str))
        assert('Order' in data and isinstance(data['Group'],str))
    def fromValues(table,Group,Location,Name,Order):
        data = {'ID': str( uuid.uuid5(uuid.NAMESPACE_OID, '\t'.join([Group,Location,Name])) ),
                'Group': Group,
                'Location': Location,
                'Name': Name,
                'Order': Order
               }
        return(GroceryArea(table,data))

class GroceryList(dynamoDB.DynamoItem):
    def validate(self,data):
        super().validate(data)
        assert('Group' in data and isinstance(data['Group'],str))
        assert('DateTime' in data and isinstance(data['DateTime'],str)) #TDOD check it is a datestring
        assert('ItemCollection' in data and isinstance(data['ItemCollection'],str))
        if 'Taxable' in data:
            assert(isinstance(data['Taxable'],Boolean))
        if 'Needed' in data:
            assert(isinstance(data['Needed'],Boolean))
        if 'Item' in data:
            assert(isinstance(data['Item'],str))
        if 'PkgPrice' in data:
            assert(isinstance(data['PkgPrice'],float) or isinstance(data['PkgPrice'],int))
        if 'Size' in data:
            assert(isinstance(data['Size'],float) or isinstance(data['Size'],int))
        if 'Unit' in data:
            assert(data['Unit'] in UNITS)
    def fromValues(table,Group,DateTime,ItemCollection,Taxable=None,Needed=None,Item=None,PkgPrice=None,Size=None,Unit=None):
        data = {'ID': str( uuid.uuid5(uuid.NAMESPACE_OID, '\t'.join([Group,DateTime])) ),
                'Group': Group,
                'DateTime': DateTime,
                'ItemCollection': ItemCollection,
               }
        if Taxable: data['Taxable']=0.06125  #only define if it is taxable
        if Needed: data['Needed']=Needed
        if Item: data['Needed']=Item
        if PkgPrice: data['Needed']=PkgPrice
        if Size: data['Needed']=Size
        if Unit: data['Needed']=Unit
        return(GroceryList(table,data))

class GroceryUser(dynamoDB.DynamoItem):
    def validate(self,data):
        super().validate(data)
        assert('Email' in data and isinstance(data['Email'],str))
        assert('Phone' in data and isinstance(data['Phone'],str)) #TODO check if actual phone number
        assert('FirstName' in data and isinstance(data['FirstName'],str))
        assert('LastName' in data and isinstance(data['LastName'],str))
        assert('Street' in data and isinstance(data['Street'],str))
        assert('Town' in data and isinstance(data['Town'],str))
        assert('State' in data and isinstance(data['State'],str)) #TODO check if valid state
        assert('Zipcode' in data and isinstance(data['Zipcode'],str)) #TODO check if valid Zipcode
        assert('Country' in data and isinstance(data['Country'],str))
        assert('Password' in data and isinstance(data['Password'],str))
        assert('SecretQuestion' in data and isinstance(data['SecretQuestion'],str))
        assert('SecretAnswer' in data and isinstance(data['SecretAnswer'],str))
        if 'AgreedToTerms' in data:
            assert(isinstance(data['AgreedToTerms'],str))
        if 'EmailActive' in data:
            assert(isinstance(data['EmailActive'],str)) #datetime email was activated
        if 'PhoneActive' in data:
            assert(isinstance(data['PhoneActive'],str)) #datetime phone number was activated
    def fromValues(table,Email,Phone,FirstName,LastName,Street,Town,State,Zipcode,Country,Password,SecretQuestion,SecretAnswer,AgreedToTerms=None,EmailActive=None,PhoneActive=None):
        data = {'ID': str(uuid.uuid4()),
                'Email': Email,
                'Phone': Phone,
                'FirstName': FirstName,
                'LastName': LastName,
                'Street': Street,
                'Town': Town,
                'State': State,
                'Zipcode':Zipcode,
                'Country': Country,
                'Password': Password,  #TODO use encryption
                'SecretQuestion': SecretQuestion,
                'SecretAnswer': SecretAnswer,
               }
        if AgreedToTerms: data['AgreedToTerms']=AgreedToTerms
        if EmailActive: data['EmailActive']=EmailActive
        if PhoneActive: data['PhoneActive']=PhoneActive
        return(GroceryUser(table,data))

class GroceryGroup(dynamoDB.DynamoItem):
    def validate(self,data):
        super().validate(data)
        assert('Group' in data and isinstance(data['Group'],str))
        assert('Owner' in data and isinstance(data['Owner'],str))
        assert('Users' in data and isinstance(data['Users'],list))
    def fromValues(table,Group,Owner,Users):
        data = {'ID': str(uuid.uuid4()),
                'Group': Group,
                'Owner': Owner,
                'Users': Users,
               }
        return(GroceryGroup(table,data))

if __name__ == "__main__":
    newtable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Items','ID',GroceryItem)
    GroceryItem.fromValues(newtable,'nwalsh','01354321','Fresh Strawberries','Wishart Farms',2,'lb','Strawberries').save()
    GroceryItem.fromValues(newtable,'nwalsh','01354323','Fresh Strawberries','Dole',1,'lb','Strawberries').save()
    GroceryItem.fromValues(newtable,'nwalsh','01354322','Turkey sliced Ultra thin','Wellesley Farms',3,'lb','Turkey, sliced').save()
    GroceryItem.fromValues(newtable,'nwalsh','01354324','Strawberry Preserves',"Smucker's",18,'oz','Strawberries').save()
    myget=newtable.get("nwalsh\tFresh Strawberries\tDole\t1\tlb",toBeHashed=True)
    myget.set('Barcode','0123214')
    #myget.set('ItemCollection','Fruit')
    print(myget)
    #newtable.delete()

    newtable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Areas','ID', GroceryArea)
    GroceryArea.fromValues(newtable,'nwalsh','Home','Fridge',1).save()
    GroceryArea.fromValues(newtable,'nwalsh','Home','Cabinets',2).save()
    GroceryArea.fromValues(newtable,'nwalsh',"BJ's",'Fruits and Veggies',4).save()
    GroceryArea.fromValues(newtable,'nwalsh',"BJ's",'Meats and Yogurt',5).save()
    GroceryArea.fromValues(newtable,'nwalsh','Stop and Shop','Fruits and Veggies',1).save()
    GroceryArea.fromValues(newtable,'nwalsh','Stop and Shop','Bread',4).save()

    newtable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Lists','ID', GroceryList)
    GroceryList.fromValues(newtable,'nwalsh','2018-01-18 9:12 AM','Strawberries').save()

    newtable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Users','ID', GroceryUser)
    GroceryUser.fromValues(newtable,'nwalsh@alumni.brown.edu','16173010740','Nathan','Walsh','3 Mathieu Dr','Westborough','MA','01581','United States of America','test','2018-01-18','Who is your best friend?','Alison').save()
    GroceryUser.fromValues(newtable,'walsha@alumni.brown.edu','16177925260','Alison','Walsh','3 Mathieu Dr','Westborough','MA','01581','United States of America','test','2018-01-18','Who is your best friend?','Nathan').save()


    newtable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Users','ID', GroceryGroup)
    GroceryGroup.fromValues(newtable,'nwalsh','1',['1','2']).save()
    
