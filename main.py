from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from pymongo import MongoClient
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv('.env')
username = os.getenv('username')
password = os.getenv('password')

DATABASE_NAME = "exceed04"
COLLECTION_NAME = "hotelFern"
MONGO_DB_URL = f"mongodb://{username}:{password}@mongo.exceed19.online"


class Reservation(BaseModel):
    name : str
    start_date: date
    end_date: date
    room_id: int


client = MongoClient(MONGO_DB_URL)

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create sample data
# collection.insert_one({
#     "name": "Pluto",
#     "start_date": "2016-07-24",
#     "end_date": "2016-07-24",
#     "room_id": 1
# })

# print(date(2022,3,3))
# print("2016-05-19">"2016-05-20")

def room_available(room_id: int, start_date: str, end_date: str):
    query={"room_id": room_id,
           "$or": 
                [{"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": start_date}}]},
                 {"$and": [{"start_date": {"$lte": end_date}}, {"end_date": {"$gte": end_date}}]},
                 {"$and": [{"start_date": {"$gte": start_date}}, {"end_date": {"$lte": end_date}}]}]
            }
    
    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)

    return not len(list_cursor) > 0


@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name:str):
    results = []
    cursor = collection.find({"name": name}, {"_id": False})
    for result in cursor:
        # print(type(result))
        results.append(result)
    return {'result': results}
    # raise HTTPException(400, f"There is no reservation with this name {name}")

@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    results = []
    cursor = collection.find({"room_id": room_id}, {"_id": 0})
    for result in cursor:
        results.append(result)
    return {'result': results}
    # raise HTTPException(400, f"There is no reservation with this room id {room_id}")

@app.post("/reservation")
def reserve(reservation : Reservation):
    rsv = reservation.dict()
    rsv['start_date'] = str(rsv['start_date'])
    rsv['end_date'] = str(rsv['end_date'])
    # print(rsv)
    # print(room_available(rsv['room_id'], rsv['start_date'], rsv['end_date']))
    room = (rsv['room_id']>=1 and rsv['room_id']<=10)
    dateCheck = rsv['start_date'] <= rsv['end_date']
    if(room_available(rsv['room_id'], rsv['start_date'], rsv['end_date']) and room and dateCheck):
        collection.insert_one(rsv)
        return "success reserving"
    else:
        raise HTTPException(400, "Can not make the reservation")

@app.put("/reservation/update")
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    rsv = reservation.dict()
    rsv['start_date'] = str(rsv['start_date'])
    rsv['end_date'] = str(rsv['end_date'])
    newStart = str(new_start_date)
    newEnd = str(new_end_date)
    dateCheck = newStart <= newEnd
    if(room_available(rsv['room_id'], newStart, newEnd) and dateCheck):
        collection.update_one(rsv, {"$set": {"start_date": newStart, "end_date": newEnd}})
        return "Updated"
    else:
        raise HTTPException(400, "Can not update")
    

@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
    rsv = reservation.dict()
    rsv['start_date'] = str(rsv['start_date'])
    rsv['end_date'] = str(rsv['end_date'])
    collection.delete_one(rsv)
    return "Deleted"