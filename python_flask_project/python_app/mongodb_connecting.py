from pymongo import MongoClient

def get_mongo_data():
    # MongoDB 서버에 연결
    client = MongoClient('mongodb://localhost:27017/')
    db = client['car_recalls']
    collection = db['recalls']
    
    # MongoDB에서 데이터 조회
    mongo_data = list(collection.find({}, {'_id': False}))  # _id 필드를 제외하고 조회
    
    return mongo_data