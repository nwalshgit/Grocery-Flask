import decimal, uuid
import dynamoDB

UNITS={'mg':{},'g':{},'lb':{},'oz':{},'mL':{},'L':{},'gal':{},'floz':{},'ea':{},'dz':{},}
ITEMSTATUS={'Needed':{},'Discontinued':{},'Purchased':{},}

class GroceryItem(dynamoDB.DynamoItem):
    '''Items can be at home with details or as part of a list'''
    def validate(self,data):
        #print("Groceryitem.validate",data)
        super().validate(data)
        assert('UserGroup' in data and isinstance(data['UserGroup'],str))
        assert('Name' in data and isinstance(data['Name'],str))
        assert('PkgPrice' in data)
        assert(isinstance(data['PkgPrice'],float) or isinstance(data['PkgPrice'],int) or isinstance(data['PkgPrice'],decimal.Decimal))
        assert('Size' in data)
        assert(isinstance(data['Size'],float) or isinstance(data['Size'],int) or isinstance(data['Size'],decimal.Decimal))
        assert('Unit' in data and data['Unit'] in UNITS)
        assert('Locations' in data and isinstance(data['Locations'],list))
        assert('ItemGroup' in data and isinstance(data['ItemGroup'],str))
        assert('Manufacturer' in data and isinstance(data['Manufacturer'],str))
        if 'Taxable' in data:
            assert(isinstance(data['Taxable'],float) or isinstance(data['Taxable'],decimal.Decimal))
        if 'Status' in data:
            assert(data['Status'] in ITEMSTATUS)
        if 'ListDate' in data:
            assert(isinstance(data['ListDate'],str)) #TODO make sure it is a dattime in str format
        if 'Home' in data:
            assert(isinstance(data['Home'],bool))
        if 'Barcode' in data:
            assert(isinstance(data['Barcode'],str))
        if 'Fees' in data:
            assert(isinstance(data['Fees'],float) or isinstance(data['Fees'],int) or isinstance(data['Fees'],decimal.Decimal))
    def fromValues(table,UserGroup,Name,PkgPrice,Size,Unit,Locations,ItemGroup,Manufacturer,Taxable=False,Status=False,ListDate=False,Home=False,Barcode=False,Fees=False):
        data = {'ID': str( uuid.uuid4() ),
                'UserGroup': UserGroup,
                'Name': Name,
                'PkgPrice': PkgPrice,
                'Size' : Size,
                'Unit' : Unit,
                'Locations' : Locations,
                'ItemGroup': ItemGroup,
                'Manufacturer': Manufacturer,
               }
        if Taxable: data['Taxable']=0.06125  #only define if it is taxable
        if Status : data['Status']=Status
        if ListDate : data['ListDate']=ListDate
        if Home : data['Home']=True
        if Barcode: data['Barcode']=Barcode
        if Fees : data['Fees']=Fees
        #print("fromValues",data)
        return(GroceryItem(table, data))
    def set(self,key,value):
        print("Setting",key,"to",value)
        assert(key not in ['ID','UserGroup'])
        return(super().set(key,value))
    def save(self,overwrite=True):
        origdata = self.__data__
        if 'Fees' in self.__data__: self.__data__['Fees']=decimal.Decimal(self.__data__['Fees'])
        if 'Taxable' in self.__data__: self.__data__['Taxable']=decimal.Decimal(self.__data__['Taxable'])
        if 'Size' in self.__data__: self.__data__['Size']=decimal.Decimal(self.__data__['Size'])
        if 'PkgPrice' in self.__data__: self.__data__['PkgPrice']=decimal.Decimal(self.__data__['PkgPrice'])
        response=super().save(overwrite)
        self.__data__ = origdata
        return(response)

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
        assert('BirthDate' in data and isinstance(data['BirthDate'],str)) #TODO check if valid date
        assert('Password' in data and isinstance(data['Password'],str))
        assert('SecretQuestion' in data and isinstance(data['SecretQuestion'],str))
        assert('SecretAnswer' in data and isinstance(data['SecretAnswer'],str))
        if 'AgreedToTerms' in data:
            assert(isinstance(data['AgreedToTerms'],str))
        if 'EmailActive' in data:
            assert(isinstance(data['EmailActive'],str)) #datetime email was activated
        if 'PhoneActive' in data:
            assert(isinstance(data['PhoneActive'],str)) #datetime phone number was activated
    def fromValues(table,Email,Phone,FirstName,LastName,Street,Town,State,Zipcode,Country,BirthDate,Password,SecretQuestion,SecretAnswer,AgreedToTerms=None,EmailActive=None,PhoneActive=None):
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
                'BirthDate': BirthDate,
                'Password': Password,  #TODO use encryption
                'SecretQuestion': SecretQuestion,
                'SecretAnswer': SecretAnswer,
               }
        if AgreedToTerms: data['AgreedToTerms']=AgreedToTerms
        if EmailActive: data['EmailActive']=EmailActive
        if PhoneActive: data['PhoneActive']=PhoneActive
        return(GroceryUser(table,data))
    def save(self,overwrite=False):
        if overwrite: #updating a user, so already have ID, TODO make sure ID not already used
            super().save(overwrite=True)
        else: #Creating a new user, so make sure email and phone doesn't clash
            fe="Email=:e or Phone=:p"
            eav={':e': self.__data__['Email'], ':p': self.__data__['Phone']}
            pe='ID, Email, Phone'
            ean=None
            items=self.table.scan(fe,eav,pe,ean)
            if items == []:
                return(super().save())
            else:
                return(None)

class GroceryGroup(dynamoDB.DynamoItem):
    def validate(self,data):
        super().validate(data)
        assert('Owner' in data and isinstance(data['Owner'],str))
        assert('Users' in data and isinstance(data['Users'],list))
    def fromValues(table,Owner,Users,ID=None ):
        if not ID: ID=str(uuid.uuid4())
        data = {'ID': ID,
                'Owner': Owner,
                'Users': Users,
               }
        return(GroceryGroup(table,data))

if __name__ == "__main__":
    usertable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Users','ID', GroceryUser)
    GroceryUser.fromValues(usertable,'nwalsh@alumni.brown.edu','16173010740','Nathan','Walsh','3 Mathieu Dr','Westborough','MA','01581','United States of America','1973-05-02','test','Who is your best friend?','Alison','2018-01-18','2018-01-18','2018-01-18').save()
    GroceryUser.fromValues(usertable,'walsha@alumni.brown.edu','16177925260','Alison','Walsh','3 Mathieu Dr','Westborough','MA','01581','United States of America','1971-07-06','test','Who is your best friend?','Nathan').save()
    nw=usertable.scan("Email=:e",{':e': 'nwalsh@alumni.brown.edu'},'ID')[0]['ID']
    aw=usertable.scan("Email=:e",{':e': 'walsha@alumni.brown.edu'},'ID')[0]['ID']

    grouptable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Groups','ID', GroceryGroup)
    usergroup=GroceryGroup.fromValues(grouptable,nw,[nw,aw],'nwalsh').save(overwrite=True)
   
    areatable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Areas','ID', GroceryArea)
    hf=GroceryArea.fromValues(areatable,usergroup,'Home','Fridge',1).save()
    hc=GroceryArea.fromValues(areatable,usergroup,'Home','Cabinets',2).save()
    bf=GroceryArea.fromValues(areatable,usergroup,"BJ's",'Fruits and Veggies',4).save()
    bm=GroceryArea.fromValues(areatable,usergroup,"BJ's",'Meats and Yogurt',5).save()
    sf=GroceryArea.fromValues(areatable,usergroup,'Stop and Shop','Fruits and Veggies',1).save()
    sd=GroceryArea.fromValues(areatable,usergroup,'Stop and Shop','Deli',4).save()

    itemtable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Items','ID',GroceryItem)
    GroceryItem.fromValues(itemtable,usergroup,'Fresh Strawberries',0.0,2,'lb',[hf,bf,sf],'Strawberries',"Wishart Farms",Home=True,Barcode='012345').save()
    GroceryItem.fromValues(itemtable,usergroup,'Fresh Strawberries',0.0,1,'lb',[hf,bf,sf],'Strawberries',"Dole",Home=True).save()
    GroceryItem.fromValues(itemtable,usergroup,'Turkey sliced Ultra thin',0.0,3,'lb',[hf,bm,sd],'Turkey, sliced',"Wellesley Farms",Home=True).save()
    i1=GroceryItem.fromValues(itemtable,usergroup,'Strawberry Preserves',0.0,18,'oz',[hf,bf,sf],'Strawberries',"Smucker's",Home=True).save()

    print(i1)
    myget=itemtable.get(i1)
    myget.set('Barcode','0123214')
    myget.set('ItemGroup','Fruit')
    print(myget)
    #newtable.delete()

