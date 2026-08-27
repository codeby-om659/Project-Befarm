import mysql.connector
import requests
import random
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status
import uuid
from datetime import datetime #venv/Scripts/Activate.ps1   cd fastapi-project 
from fastapi import FastAPI,HTTPException     #  , , uvicorn project:app --reload
from pydantic import BaseModel
app=FastAPI(title="Mandi procurement API")
#cors setup(frontend se connet karne ke liye)
app.add_middleware (
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#temporary memory otp store karne ke liye(production mai redis ya database ka use kare)
otp_db={}
#fast2sms api key
FAST2SMS_API_KEY="CJcQDPtYox7MZFI0l63HvyzKj81NLbTEqg9mAnpUW5hOwBfRks8BpXDSbZ0FgGHy5mjAVYlPrTwaUtn1"

class PhoneRequest(BaseModel):
    mobile_number:str
    

class VerifyOTPRequest(BaseModel):
    mobile_number:str
    otp:str

    #otp send karne ka endpoiint
@app.post("/send-otp/")
async def send_otp(request: PhoneRequest):
    #4 digit ka random otp generate kare
    otp=str(random.randint(1000,9999))
    phone=request.mobile_number
    #fast2sms api call
    url="https://www.fast2sms.com/dev/bulkV2"
    payload={
        "message":f"your otp is{otp}",
        "variable_values":otp,
        "route":"otp",
        "numbers":phone
    }
    headers={
        'authorization':FAST2SMS_API_KEY,
        'content-type':"application/x-www-form-urlencoded"
    }
    try:
        response=requests.post(url,data=payload,headers=headers)
        res_data=response.json()
        print("fast2sms rESPONSE:",res_data)

        if res_data.get("return"):
            #otp memory mein save karein verify karne ke liye
            otp_db[phone]=otp
            return {"status":"success","message":f"OTP sent to{phone}"}
        else:
            raise HTTPException(status_code=400,detail="smsbhejne mai dekkat aayi.")

    except Exception as e:
        print(f"Error sending sms:{e}")
        #testing ke liye agar apikey na ho to terminal par print kare
        otp_db[phone]=otp
        print(f"Generated OTP for {phone}:{otp}")
        return {"status":"testing mode","message":"otp generratedon server terminal","otp_for_test":otp}
    
    #otp verify karne ke liye end point
@app.post("/verify-otp/")
async def verify_otp(request:VerifyOTPRequest):
    stored_otp=otp_db.get(request.mobile_number)

    if not stored_otp:
        raise HTTPException(status_code=400,detail="pehle otp gnerate kare")
    if stored_otp==request.otp:
        del otp_db[request.mobile_number]#verification ke bad delete kare
        return {"status":"success","message":"phone number successfully vrified"}
    else:
        raise HTTPException(status_code=400,detail="galat otp fir se try kare")

        
#batabase connection#,

MYSQL_CONFIG={
    "host":"localhost",
    "user":"root",#my sql username
    "password":"omverma67895@",#
    "database":"mandi_database"
}
# data vase connection helper
def get_db():
    try:
        return mysql.connector.connect(**MYSQL_CONFIG)
    except mysql.connector.Error as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database ConnectionError:{err}"
        )

#pydantic schemas(data validation)
class farmerCreate(BaseModel):
    farmer_id:str
    farmer_name:str
    mobile_number:str
    aadhar_number:str
    mandi_name:str

class Cropcreate(BaseModel):
    farmer_id:str
    crop_type:str
    estimated_quintal:float
    

#api Endpoint
@app.get("/")
def home():
    return{"message":"mandi portal API is running"}

#end point1:Register new farmer
@app.post("/register-farmer")
def register_farmer(farmer:farmerCreate):
    db=get_db()
    cursor=db.cursor()

    query="""
    INSERT INTO farmers (farmer_id,farmer_name,mobile_number,aadhar_number,mandi_name)
    VALUES(%s,%s,%s,%s,%s)
    """
    values=(
        farmer.farmer_id,
        farmer.farmer_name,
        farmer.mobile_number,
        farmer.aadhar_number,
        farmer.mandi_name
    )
    try:
        cursor.execute(query,values)
        db.commit()
        return{"status":"sucess","message":"farmer registered successfully","farmer_id":farmer.farmer_id}
    except mysql.connector.Error as err:
        db.rollback()
        raise HTTPException(status_code=400,detail=f"registration failed:{err}")
    finally:
        cursor.close()
        db.close()
    
#endpoint 2 create
@app.post("/book-crop-slot")
def book_slot(crop:Cropcreate):
    db=get_db()
    cursor=db.cursor()
    #random unique token generate,from date and time,uuid
    #format:TOK-YYYYMMDD-RANDOM
    now=datetime.now()
    date_part=now.strftime("%y%m%d") #current date
    rand_part=str(uuid.uuid4())[:4].upper()

    generated_token=f"TOK-{date_part}-{rand_part}"
    query="""
    INSERT INTO farmers_crops(farmer_id,crop_type,estimated_quintal,token_id)
    VALUES(%s,%s,%s,%s)
    """
    values=(
        crop.farmer_id,
        crop.crop_type,
        crop.estimated_quintal,
        generated_token
    )
    try:
        cursor.execute(query,values)
        db.commit()
        return {
            "status":"Success",
            "message":"crop slot booked successfully",
            "token_id": generated_token,
            "farmer_id":crop.farmer_id                 
        }
    except mysql.connector.Error as err:
        db.rollback()
        raise HTTPException(status_code=400,detail=f"booking failed:{err}")
    finally:
        cursor.close()
        db.close()

#end point 3 :get all crops booked by a specific farmer
@app.get("/farmer-crop/{farmer_id}")
def get_farmer_crops(farmer_id:str):
    db=get_db()
    cursor=db.cursor(dictionary=True)

    query="select* from farmers_crops WHERE farmer_id=%s"
    cursor.execute(query,(farmer_id,))
    crops=cursor.fetchall()

    cursor.close()
    db.close()
    if not crops:
        raise HTTPException(status_code=404,detail="no crops/slot found for this farmer id")

    return {
        "farmer_id":farmer_id,
        "total_crops":len(crops),
        "crops_data":crops
    }  


