import datetime, decimal, json, time, uuid
import boto3, botocore

local_dynamodb=False
if local_dynamodb:
    dynamodb = boto3.resource('dynamodb',endpoint_url="http://localhost:8000")
else:
    dynamodb = boto3.resource('dynamodb',region_name='us-east-2')

#Helper class to convert a DynamoDB item to JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

class DynamoItem():
    def validate(self,data):
        #print("DynamoItem.validate")
        #print(self.table)
        assert(self.table.hash_key in data)
    def __init__(self, table, data, valueToHash=None):
        #print("DynamoItem.__init__")
        self.table=table
        if valueToHash and valueToHash in data:
            #print("DynamoItem.__init: ",data[valueToHash])
            data[table.hash_key]=str( uuid.uuid5(uuid.NAMESPACE_OID, data[valueToHash]) )
            #print("                 : ",data[table.hash_key])
        self.validate(data)
        self.__data__ = data
    def set(self,key,value):
        if isinstance(key, (list,tuple)) and not isinstance(key, str):
            print("DynamoItem.set() ignores a key that isn't a string") #really keys and values...
        else:
            self.__data__[key]=value
    def get(self,key):
        return(self.__data__[key])
    def __repr__(self):
        return(json.dumps(self.__data__, indent=4, cls=DecimalEncoder))
        #return(str(self.__data__))
    def save(self,overwrite=True):
        if overwrite==False:
            print("TODO: save with overwrite false not implemented")
            self.__data__['Updated']=str(datetime.datetime.now())
            self.__data__['Created']=self.__data__['Updated']
        self.__data__['Updated']=str(datetime.datetime.now())
        #print(self.__data__)
        response=self.table.table.put_item( Item=self.__data__ )
        return(self.__data__['ID'])

class SimpleDynamoTable():
    """DynamoDB Table with 'hash_key' as a string hash_key and no range_key"""
    def create(self,hash_key):
        response = dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {   'AttributeName': hash_key,
                    'KeyType': 'HASH' #Partition key
                },
            ],
            AttributeDefinitions=[
                {   'AttributeName': hash_key,
                    'AttributeType': 'S'  # S = String
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits':1,
                'WriteCapacityUnits':1
            }
        )
        self.table = dynamodb.Table(self.table_name)
        return(response)
    def __init__(self, table_name, hash_key, ObjectClass=DynamoItem):
        self.table_name=table_name
        self.hash_key=hash_key
        #Try to connect to an existing table
        self.table = dynamodb.Table(table_name)
        self.ObjectClass=ObjectClass
        try:
            status=self.table.table_status
        except:
            self.create(hash_key)
            status = self.table.table_status
            if self.table.table_status=="CREATING": 
                print("Creating table %s, it may take a minute."%table_name )
                while self.table.table_status=="CREATING":
                    time.sleep(2)
                    self.table = dynamodb.Table(table_name)
            assert(self.table.table_status=='ACTIVE')
        #print("Table status", self.table.table_status)
    def delete(self):
        self.table.delete()
    def get(self,hash_value,toBeHashed=False):
        #print("DynamoTable.get: ", hash_value, toBeHashed)
        if toBeHashed: hash_value=str( uuid.uuid5(uuid.NAMESPACE_OID, hash_value) )
        #print("               : ", hash_value)
        try:
            response = self.table.get_item( Key={self.hash_key:hash_value} )
        except botocore.exceptions.ClientError as e:
            print(e.response['Error']['Message'])
        else:
            if 'Item' in response:
                #item=json.dumps(response['Item'], cls=DecimalEncoder) 
                #convert string (with Decimal()) to json (with int and float)
                item=json.loads(DecimalEncoder().encode(response['Item']))
                print("GetItem succeded:",item)
                return self.ObjectClass(self,item)
            else:
                print("GetItem failed",response)
        return(None) 
    def scan(self,fe,eav,pe,ean=None):
        ScannedCount=0
        items=[]
        if ean:
            response = self.table.scan(
                FilterExpression = fe,
                ExpressionAttributeValues = eav,
                ProjectionExpression = pe,
                ExpressionAttributeNames = ean,
            )
            ScannedCount+=response['ScannedCount']
            while True:
                #do action on each item of the "page"
                for item in response[u'Items']:
                    #items.append(json.dumps(item, cls=DecimalEncoder))
                    items.append(item)
                    #print("TableScan:",item)
                #If more data then read another "page", otherwise we are done
                if response.get('LastEvaluatedKey'):
                    response = table.scan(
                        FilterExpression = filter_expression,
                        ExpressionAttributeValues = expression_attribute_values,
                        ProjectionExpression = projection_expression,
                        ExpressionAttributeNames = expression_attribute_names,
                        ExclusiveStartKey = exclusive_start_key
                    )
                    ScannedCount+=response['ScannedCount']
                else:
                    break
        else:
            response = self.table.scan(
                FilterExpression = fe,
                ExpressionAttributeValues = eav,
                ProjectionExpression = pe,
            )
            ScannedCount+=response['ScannedCount']
            while True:
                #do action on each item of the "page"
                for item in response[u'Items']:
                    #items.append(json.dumps(item, cls=DecimalEncoder))
                    items.append(item)
                    #print("Item:",item)
                #If more data then read another "page", otherwise we are done
                if response.get('LastEvaluatedKey'):
                    response = table.scan(
                        FilterExpression = filter_expression,
                        ExpressionAttributeValues = expression_attribute_values,
                        ProjectionExpression = projection_expression,
                        ExclusiveStartKey = exclusive_start_key
                    )
                    ScannedCount+=response['ScannedCount']
                else:
                    break
        print("SimpleDynamoTable Warning:",ScannedCount,"rows scanned.")
        return(items)

if __name__ == '__main__':
    print('Test')
    newtable = SimpleDynamoTable('NewTable','MyId')
    pumpkin = DynamoItem(table=newtable,data={'Name':'Pumpkin'},valueToHash='Name')
    pumpkin.set('color','orange')
    print(pumpkin)
    pumpkin.save()
    myget=newtable.get('Pumpkin',toBeHashed=True)
    print(myget)
    #newtable.delete()


def updateMovie(title,year):
    try:
        titlehash = str(uuid.uuid5(uuid.NAMESPACE_OID, title+str(year)))
        response = table.update_item(
            Key = {'titlehash':titlehash},
            UpdateExpression = "set info.rating = :r, info.plot = :p, info.actors = :a",
            #Could say:  set info.rating = info.rating + :r
            ExpressionAttributeValues = {
                ':r': decimal.Decimal(5.5),
                ':p': "Everything happens at once",
                ':a': ["Larry","Moe","Curly"],
            },
            ReturnValues="UPDATED_NEW"
        )
        print("UpdateItem rating,plot,actors succeeded:")
        print(json.dumps(response, indent=4, cls=DecimalEncoder))
    except botocore.exceptions.ClientError as e:
        print(e)
#updateMovie('Hulk',1999)

#  For Key and Attr
#begins_with(value)
#between(low,high)
#eq(value)
#gt(value)
#gte(value)
#lt(value)
#lte(value)
# For Attr only
#attribute_type(value)
#contains(value)
#exists()
#ne(value)
#not_exists()       #"attribute_not_exists(plot)"
#size()

def updateMovie2(title,year):
    print("Attempting to update an item")
    print("It should just remove first actor, but removing everything but second actor incl plot and rating.  WHY?")
    try:
        titlehash = str(uuid.uuid5(uuid.NAMESPACE_OID, title+str(year)))
        response = table.update_item(
            #Key = {'year':year, 'title':title},
            Key = {'titlehash':titlehash},
            UpdateExpression = "remove info.actors[0]",
            ConditionExpression = "size(info.actors) >= :num",
            ExpressionAttributeValues = { ':num' : 3 },
            ReturnValues="UPDATED_NEW"
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
        else:
            raise
    else:
        print("UpdateItem actors succeded:")
        print(json.dumps(response, indent=4, cls=DecimalEncoder))
#updateMovie2('Hulk',1999)

def deleteMovie(title,year):
    titlehash = str(uuid.uuid5(uuid.NAMESPACE_OID, title+str(year)))
    print("Remove this movie if rating less than 5")
    try:
        response = table.delete_item(
                Key={'titlehash':titlehash},
         ConditionExpression="info.rating <= :val",
            ExpressionAttributeValues = { ":val" : decimal.Decimal(10) },
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
        else:
            raise
    else:
        print("DeleteItem succeded:")
        print(json.dumps(response, indent=4, cls=DecimalEncoder))
#deleteMovie('Hulk',1999)

def queryMovies() :   #Uses efficient Key Indexes
    print("Find all movies from 2017")
    response = table.query(
            #We could write our own condition as a string or use built in builder
            KeyConditionExpression=boto3.dynamodb.conditions.Key('year').eq(2017)
    )
    for movie in response['Items']:
        print(movie['year'],movie['title'])

    print("Find all movies beginning with A-L")
    response = table.query(
        ProjectionExpression="#yr, title, info.genres, info.actors[0]",
        ExpressionAttributeNames={"#yr":"year" }, #This is just for Projection Expression
        #We could write our own condition as a string or use built in builder
        KeyConditionExpression=boto3.dynamodb.conditions.Key('year').eq(2017) &
                               boto3.dynamodb.conditions.Key('title').between('A','L')
    )
    for movie in response[u'Items']:
        print(movie['year'],movie['title'])
#queryMovies()

#Scan wil READ the ENTIRE database and then filter what you want.  It can get expensive!
def scanMovies1():
    #filter_expression = boto3.dynamodb.conditions.Key('year').between(2000,2020) 
    filter_expression = "((#yr > :y1) and (title >= :t1) and (title < :t2))"
    print(str(filter_expression))
    projection_expression = "#yr, title, info.rating"
    expression_attribute_names = {"#yr": "year", }
    #Read first "page"
    response = table.scan(
        FilterExpression = filter_expression,
        ExpressionAttributeValues = {':y1':2000,':t1':'Hulk',':t2':'Hull'},
        ProjectionExpression = projection_expression,
        ExpressionAttributeNames = expression_attribute_names,
    )
    #there may be more than one page of data so enclose in a loop
    while True:
        #do action on each item of the "page"
        for movie in response[u'Items']:
            print(json.dumps(movie, cls=DecimalEncoder))
        #If more data then read another "page", otherwise we are done
        if response.get('LastEvaluatedKey'):
            response = table.scan(
                FilterExpression = filter_expression,
                ProjectionExpression = projection_expression,
                ExpressionAttributeNames = expression_attribute_names,
                ExclusiveStartKey = exclusive_start_key
            )
        else:
            break
#scanMovies1()

#table.delete()

