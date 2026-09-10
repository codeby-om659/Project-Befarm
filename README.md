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
class StatusUpdateSchems(BaseModel):
    crop_id:int
    status:str

class admin_login(BaseModel):
    admin_id:str
    admin_password:str

Admin_credit={
    "om123":"om@123"
}



class VerifyOTPRequest(BaseModel):
    mobile_number:str
    otp:str

@app.post("/admin/update-status/")
def update_crop_status(data:StatusUpdateSchems):
    connection=mysql.connector.connect(**MYSQL_CONFIG)
    cursor= connection.cursor()
    try:
        
        if data.status =="approved":
            now=datetime.now()
            date_part=now.strftime("%y%m%d") #current date
            rand_part=str(uuid.uuid4())[:4].upper()
        
            token_id=f"TOK-{date_part}-{rand_part}"
            query= """
                UPDATE farmers_crops
                SET status= %s,token_id=%s
                WHERE crop_id=%s
            """
            cursor.execute(query,(token_id,data.crop_id))
            message="Booking Approved and token Generrated"
        elif data.status=="reject":
            query="""
                UPDATE farmers_crops
                SET status='%stoken_id=NULL
                WHEREcrop_id=%s
            """
            cursor.execute(query,(data.status,token_id,data.crop_id,))
            message="Booking Rejected"
        else:
            query="UPDATE farmers_crops SET status=%s WHERE crop_id=%s"
            cursor.execute(query,(data,status,data.crop_id))
        connection.commit()   
            
        return {
            "status": "success",
            "message": "Booking approved and Token generated successfully",
            "token_id":token_id
        }
    except mysql.connector.Error as err:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error:{err}")
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"server error:{str(e)}")

@app.get("/farmer/token/{farmer_id}")
def get_farmer_token(farmer_id: str):
    connection = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = connection.cursor(dictionary=True)
    
    try:
        query = """
            SELECT crop_id, crop_type, estimated_quintal, slot_date, status, token_id 
            FROM farmers_crops 
            WHERE farmer_id = %s 
            ORDER BY crop_id DESC LIMIT 1
        """
        cursor.execute(query, (farmer_id,))
        result = cursor.fetchone()
        return {"status": "success", "data": result}
    finally:
        cursor.close()
        connection.close()
         
@app.post("/Admin-Registration/")
def VerifyAdmin(Admin:admin_login):
    if Admin.admin_id in Admin_credit:
        if Admin_credit[Admin.admin_id]== Admin.admin_password:
            return {"status":"success","message":"Login successFully"}

    raise HTTPException(status_code=401,detail="Invalid Id or Passwrod")
        
    
    
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

        connection=mysql.connector.connect(**MYSQL_CONFIG)
        cursor= connection.cursor(dictionary=True)
        cursor.execute("SELECT *FROM farmers WHERE mobile_number=%s",(request.mobile_number,))
        farmer=cursor.fetchone()
        is_registered =True if farmer else False
        return {"status":"success","is_registered":is_registered,"message":"phone number successfully vrified"}
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
    status:int
    

#api Endpoint
@app.get("/")
def home():
    return{"message":"mandi portal API is running"}

@app.get("/admin/booking/")
async def get_admin_bookings():
    try:
        connection=mysql.connector.connect(**MYSQL_CONFIG)
        cursor= connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM farmers_crops ORDERR BY crop_id DESC")
        bookings=cursor.fetchall()

        toatal_bookings=len(bookings)

        total_quantity=sum(float(item.get("estimated_quintal")or 0.0)for item in bookings)
        #Activate token Count (jinka status "approned"hai aur token_id generate hai)
        active_token=len([b for b in bookings if str(b.get("status")).lower()=="approved"])
        cursor.close()
        connection.close()
        return {
            "status":"success",
            "total_bookings":toatal_bookings,
            "total_quantity":total_quantity,
            "active_tokes":active_token,
            "bookings":bookings
        }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500,detail=f"Database error:{err}")
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"server error{str(e)}")
#end point1:Register new farmer
@app.post("/register-farmer/")
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
@app.post("/book-crop-slot/")
def book_slot(crop:Cropcreate):
    db=get_db()
    cursor=db.cursor()
    #random unique token generate,from date and time,uuid
    #format:TOK-YYYYMMDD-RANDOM
    

    
    query="""
    INSERT INTO farmers_crops(farmer_id,crop_type,estimated_quintal)
    VALUES(%s,%s,%s,%s)
    """
    values=(
        crop.farmer_id,
        crop.crop_type,
        crop.estimated_quintal
        
    )
    try:
        cursor.execute(query,values)
        db.commit()
        return {
            "status":"Success",
            "message":"crop slot booked successfully",
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

