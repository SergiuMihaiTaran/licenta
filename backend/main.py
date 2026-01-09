from asyncio import sleep
from fastapi import FastAPI, HTTPException
from fastapi.params import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sqlalchemy
from faker import Faker 
fake=Faker()



from sqlalchemy import create_engine, Column, String,Integer,ForeignKey,Float,delete,DateTime,Numeric
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import or_ 
import jwt
secret="secret"
algorithm="HS256"

def generate_iban_ro():
    # Generează un IBAN de România valid matematic
    iban= fake.iban()
    iban="RO"+iban[2:]
    return iban
# encoded_jwt = jwt.encode({"id": id,
#                           "email": email}, secret,algorithm=algorithm)
# jwt.decode(encoded_jwt, "secret", algorithms=["HS256"])
security = HTTPBearer()
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    email = Column(String,unique=True)
    phone = Column(String)
    password = Column(String)
    cards = relationship("CardDB", back_populates="owner")
class CardDB(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    user_id = Column(Integer,ForeignKey("users.id"))
    name = Column(String)
    number = Column(String)
    expiration = Column(String)
    balance = Column(Float, default=0)
    iban = Column(String, default="")
    cvc = Column(String)
    owner = relationship("UserDB", back_populates="cards")
class PaymentDB(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    user_id = Column(Integer,ForeignKey("users.id"))
    amount = Column(Numeric)
    ibanFrom = Column(String,ForeignKey("cards.iban"))
    ibanTo = Column(String,ForeignKey("cards.iban"))
    typeId = Column(Integer,ForeignKey("payment_types.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
class PaymentTypeDB(Base):
    __tablename__ = "payment_types"
    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String)
Base.metadata.create_all(bind=engine) 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True, 
)

class PaymentDetails(BaseModel):
    amount: float
    iban: str
    type: str  
class UserCreate(BaseModel):
    phone: str
    email: str
    password: str
class CardInfo(BaseModel):
    name: str
    number: str
    expiration: str
    cvc: str
class UserLogin(BaseModel):
    identifier: str  # Can be email or phone
    password: str
def delete_user_cards(user_id: int):
    db = SessionLocal()
    db.query(CardDB).filter(CardDB.user_id == user_id).delete()
    db.commit()
    db.close()
@app.post("/register")
async def register(user: UserCreate):
    print("Received registration request for:", user.email, user.phone)
    db = SessionLocal()
    existing_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if existing_user:
        db.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = UserDB(phone=user.phone, email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.close()
    return {"success": True, "message": "User registered successfully!"}
@app.post("/login")
async def login(credentials: UserLogin):
    db = SessionLocal()
    user = db.query(UserDB).filter(
        or_(
            UserDB.email == credentials.identifier, 
            UserDB.phone == credentials.identifier
        )
    ).first()
    
    if not user or user.password != credentials.password:
        db.close()
        raise HTTPException(status_code=400, detail="Invalid email/phone or password")
    
    token = jwt.encode({"id": user.id, "email": user.email}, secret, algorithm=algorithm)
    db.close()
    return {
        "token": token, 
        "id": user.id,
        "email": user.email
    }
@app.post("/card")
async def add_card(card: CardInfo,auth: HTTPAuthorizationCredentials = Depends(security)):
    token = auth.credentials
    print(jwt.decode(token, secret, algorithms=[algorithm]))
    print("Received card info:", card)
    delete_user_cards(jwt.decode(token, secret, algorithms=[algorithm])["id"])
    try:
        db = SessionLocal()
        new_card = CardDB(
            user_id=jwt.decode(token, secret, algorithms=[algorithm])["id"],
            name=card.name,
            number=card.number,
            expiration=card.expiration,
            cvc=card.cvc,
            iban=generate_iban_ro()
        )
        db.add(new_card)
        
        db.commit()
        db.close()
    except Exception as e:
        print("Error adding card:", e)
        raise HTTPException(status_code=400, detail="Invalid card data")
    return {"success": True, "message": "Card added successfully!"}
@app.get("/card/mininmal_info")
async def get_card_minimal_info(auth: HTTPAuthorizationCredentials = Depends(security)):
    token = auth.credentials
    user_id = jwt.decode(token, secret, algorithms=[algorithm])["id"]
    db = SessionLocal()
    cards = db.query(CardDB).filter(CardDB.user_id == user_id).first()
    result = {"balance": cards.balance, "name": cards.name, "number": cards.number[-4:]} if cards else {}
    db.close()
    return result
@app.post("/payment")
async def make_payment(details: PaymentDetails,auth: HTTPAuthorizationCredentials = Depends(security)):
    token = auth.credentials
    user_id = jwt.decode(token, secret, algorithms=[algorithm])["id"]
    db = SessionLocal()
    card = db.query(CardDB).filter(CardDB.user_id == user_id).first()
    if not card:
        db.close()
        raise HTTPException(status_code=400, detail="No card found")
    amount = details.amount
    if amount <= 0:
        db.close()
        raise HTTPException(status_code=400, detail="Amount must be positive")

    if(len(details.iban)<16 or details.type==""):
        db.close()
        raise HTTPException(status_code=400, detail="Invalid data")
        
    if card.balance < amount:
        db.close()
        raise HTTPException(status_code=400, detail="Insufficient funds")
    card.balance -= amount
    new_payment = PaymentDB(
            user_id=user_id,
            amount=amount,
            ibanFrom=card.iban,
            ibanTo=details.iban,
            typeId=getTypeId(details.type)
        )
        
    db.add(new_payment)
    db.commit()
    db.close()
    return {"success": True, "message": "Payment successful"}
def getTypeId(type_name: str) -> int:
    db = SessionLocal()
    payment_type = db.query(PaymentTypeDB).filter(PaymentTypeDB.name == type_name).first()
    if not payment_type:
        return -1
    db.close()
    return payment_type.id
def populate_payment_types():
    db = SessionLocal()
    types = ["Utility", "Rent", "Food", "Entertainment", "Transport","Other"]
    for type_name in types:
        existing_type = db.query(PaymentTypeDB).filter(PaymentTypeDB.name == type_name).first()
        if not existing_type:
            new_type = PaymentTypeDB(name=type_name)
            db.add(new_type)
    db.commit()
    db.close()
def populate_with_users_and_cards():
    db = SessionLocal()
    for i in range(5):
        email = f"user{i}@example.com"
        password = f"password{i}"
        user = UserDB(email=email, password=password)
        db.add(user)
        db.commit()
        card = CardDB(
            user_id=user.id,
            name=f"Card {i}",
            number=f"123456789012345{i}",
            balance=1000.0,
            expiration="12/25",
            cvc="123",
            iban=generate_iban_ro()
        )
        db.add(card)
    db.commit()
    db.close()
# Add this to main.py
@app.get("/card")
async def get_card_full_info(auth: HTTPAuthorizationCredentials = Depends(security)):
    token = auth.credentials
    user_id = jwt.decode(token, secret, algorithms=[algorithm])["id"]
    db = SessionLocal()
    card = db.query(CardDB).filter(CardDB.user_id == user_id).first()
    
    if not card:
        db.close()
        raise HTTPException(status_code=404, detail="Card not found")
        
    # Return all details including CVC and Expiration
    result = {
        "name": card.name,
        "number": card.number,
        "expiration": card.expiration,
        "cvc": card.cvc,
        "balance": card.balance,
        "iban": card.iban
    }
    db.close()
    return result
# populate_with_users_and_cards()
# populate_payment_types()