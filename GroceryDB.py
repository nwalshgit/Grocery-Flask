import decimal, uuid
import dynamoDB

UNITS={'mg':{},'g':{},'lb':{},'oz':{},'mL':{},'L':{},'gal':{},'floz':{},'ea':{},'dz':{},}

class GroceryItem(dynamoDB.DynamoItem):
    def validate(self,data):
        #print("Groceryitem.validate")
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
        data = {'ID': str( uuid.uuid3(uuid.NAMESPACE_OID, "\t".join([Group,Name,Manufacturer,str(Size),Unit])) ),
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
        super.validate(data)
        assert('Group' in data)
        assert('Location' in data)
        assert('Name' in data)
        assert('Order' in data)
    def fromValues(table,Group,Location,Name,Order):
        data = {'ID': str( uuid.uuid3(uuid.NAMESPACE_OID, '\t'.join([Group,Location,Name])) ),
                'Group': Group,
                'Location': Location,
                'Name': Name,
                'Order': Order
               }
        return(GroceryItem(table,data))

if True:
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
    GroceryArea.fromValues(newtable,'2018-01-18 9:12 AM','Strawberries').save()

    newtable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Users','ID', GroceryUser)
    GroceryArea.fromValues(newtable,'nwalsh@alumni.brown.edu','16173010740','Nathan','Walsh','3 Mathieu Dr','Westborough','MA','United States of America','test','2018-01-18','Who is your best friend?','Alison').save()
    GroceryArea.fromValues(newtable,'walsha@alumni.brown.edu','16177925260','Alison','Walsh','3 Mathieu Dr','Westborough','MA','United States of America','test','2018-01-18','Who is your best friend?','Nathan').save()


    newtable = dynamoDB.SimpleDynamoTable('GroceryFlaskApp-WebEnv-Users','ID', GroceryGroup)
    GroceryArea.fromValues(newtable,'nwalsh',1,[1,2]).save()
    
