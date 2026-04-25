from asyncio import sleep

from fastapi import FastAPI, HTTPException
from fastapi.params import Depends
import numpy as np
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from RecomandationSystem.KNNClasification import get_neighbor_spending, get_neighbor_spending
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from RecomandationSystem.loadDataset import  generate_category_recommendations, loadDataset, get_KMeans_recommandations, print_neighbor_spending_from_df
import sqlalchemy
import joblib
from faker import Faker 
fake=Faker()

from sqlalchemy import create_engine, Column, String,Integer,ForeignKey,Float,delete,DateTime,Numeric,Date
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import or_ 
import jwt
secret="secret"
algorithm="HS256"
users_data_location='RecomandationSystem/data/users_data.csv'
payments_data_location='RecomandationSystem/data/transactions_data_categorized.csv'
def get_age_from_dateOfBirth(dob_str):
    age = 0
    if dob_str:
        from datetime import date
        today = date.today()
        age = today.year - dob_str.year - ((today.month, today.day) < (dob_str.month, dob_str.day))
    return age
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
    credit_score = Column(Integer, default=0)
    debt=Column(Float, default=0)
    date_of_birth = Column(Date, nullable=True)
    yearly_income=Column(Float, default=0)
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
    credit_score: str
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
    
    new_user = UserDB(phone=user.phone, email=user.email, password=user.password,credit_score=int(user.credit_score))
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
@app.get("/recommendations")
async def get_recommendations(auth: HTTPAuthorizationCredentials = Depends(security)):
    token = auth.credentials
    user_id = jwt.decode(token, secret, algorithms=[algorithm])["id"]
    result=get_user_profile_csv(user_id)
    print(result)
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
    types = [
    "Food & Dining",
    "Shopping & Retail", 
    "Health & Wellness",
    "Transportation",
    "Utilities & Services",
    "Entertainment & Travel",
    "Home & Garden",
    "Electronics & Tech",
    "Industrial & Business",
    "Other"
]
    for type_name in types:
        existing_type = db.query(PaymentTypeDB).filter(PaymentTypeDB.name == type_name).first()
        if not existing_type:
            new_type = PaymentTypeDB(name=type_name)
            db.add(new_type)
    db.commit()
    db.close()
import random
from datetime import date, timedelta

def populate_with_users_and_cards():
    db = SessionLocal()
    for i in range(5):
        email = f"user{i}@example.com"
        password = f"password{i}"
        
        # Generăm date de test variate pentru a avea clustere interesante
        # Scor credit între 300 și 850
        test_credit_score = random.randint(400, 820)
        # Venit anual între 20.000 și 150.000
        test_income = random.uniform(25000, 120000)
        # Datorii între 0 și 50.000
        test_debt = random.uniform(0, 40000)
        # Data nașterii (vârsta între 20 și 65 ani)
        days_ago = random.randint(365*20, 365*65)
        test_dob = date.today() - timedelta(days=days_ago)

        user = UserDB(
            email=email, 
            password=password,
            phone=f"0722{random.randint(100000, 999999)}",
            credit_score=test_credit_score,
            yearly_income=test_income,
            debt=test_debt,
            date_of_birth=test_dob
        )
        
        db.add(user)
        db.commit() # Commit aici pentru a genera user.id

        card = CardDB(
            user_id=user.id,
            name=f"Card Premium {i}" if test_credit_score > 700 else f"Card Standard {i}",
            number=f"424212345678901{i}",
            balance=random.uniform(1000.0, 5000.0),
            expiration="12/28",
            cvc=str(random.randint(100, 999)),
            iban=generate_iban_ro()
        )
        db.add(card)
    
    db.commit()
    db.close()
    print("Baza de date a fost populată cu succes cu profiluri hibride (Demografice + Carduri).")
@app.get("/card")
async def get_card_full_info(auth: HTTPAuthorizationCredentials = Depends(security)):
    token = auth.credentials
    user_id = jwt.decode(token, secret, algorithms=[algorithm])["id"]
    db = SessionLocal()
    card = db.query(CardDB).filter(CardDB.user_id == user_id).first()
    
    if not card:
        db.close()
        raise HTTPException(status_code=404, detail="Card not found")
        
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
def insert_test_payments(user_id: int):
    db = SessionLocal()
    card = db.query(CardDB).filter(CardDB.user_id == user_id).first()
    if not card:
        print("Utilizatorul nu are card, nu putem insera plăți.")
        return
    test_data = [
        {"amount": 150.75, "type": "Food & Dining"},
        {"amount": 45.00,  "type": "Food & Dining"},
        {"amount": 300.00, "type": "Transportation"},
        {"amount": 20.00,  "type": "Shopping & Retail"},
    ]

    for item in test_data:
        type_id = getTypeId(item["type"]) # Folosim funcția ta existentă
        
        new_payment = PaymentDB(
            user_id=user_id,
            amount=item["amount"],
            ibanFrom=card.iban,
            ibanTo=generate_iban_ro(), # Destinație random
            typeId=type_id
        )
        db.add(new_payment)
        
    db.commit()
    print(f"Am inserat {len(test_data)} tranzacții pentru user {user_id}")
    db.close()
# def get_age_from_dateOfBirth(dob_string):
#     """Calculează vârsta dintr-un string de tip dată (ex: '1990-05-15')."""
#     try:
#         dob = datetime.strptime(dob_string, "%Y-%m-%d")
#         today = datetime.today()
#         return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
#     except:
#         return 0

def get_user_profile(user_id):
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user:
            return None
        age= get_age_from_dateOfBirth(user.date_of_birth)
        query = (
            db.query(
                PaymentTypeDB.name.label("category"),
                func.sum(PaymentDB.amount).label("total_amount")
            )
            .join(PaymentTypeDB, PaymentDB.typeId == PaymentTypeDB.id)
            .filter(PaymentDB.user_id == user_id)
            .group_by(PaymentTypeDB.name)
            .all()
        )
        
        profile = {
            "current_age": age if age > 0 else 30, 
            "yearly_income": float(user.yearly_income),
            "total_debt": float(user.debt),
            "credit_score": int(user.credit_score)
        }
        for category, total in query:
            profile[category] = float(total)
            
        return profile
    finally:
        db.close()


def get_knn_recommendations(user_id):
    global matrix
    matrix = loadDataset(user_id)
    user_profile = get_user_profile_csv(user_id)
    
    print(f"Profilul de cheltuieli pentru user {user_id}: {user_profile}")
    if not user_profile:
        print("Userul nu are tranzacții.")
        return []
    allowed_columns = [col for col in matrix.columns if col not in ['cluster_id', 'client_id']]
    user_vector = [user_profile.get(col, 0.0) for col in allowed_columns]
   # print(f"DEBUG: Vectorul final are {len(user_vector)} dimensiuni: {user_vector}")
    user_vector_np = np.array(user_vector).astype(float).reshape(1, -1)
    mean_val = np.mean(user_vector_np)
    normalized_user_vector = user_vector_np - mean_val
    neighbors = get_neighbor_spending(normalized_user_vector)
    
   # print(f"Vecinii găsiți pentru userul {user_id}: {neighbors}")
   # print(f"Categorii recomandate pentru userul {user_id}:")
    print(generate_category_recommendations(user_id, neighbors))
    return neighbors
def get_kmeans_recommendations(user_id):
    global matrix
    profile = get_user_profile_csv(user_id)
    if not profile:
        print("Userul nu are date suficiente.")
        return []
    features = [col for col in matrix.columns if col != 'cluster_id']
    user_vector = []
    for col in features:
        user_vector.append(profile.get(col, 0.0))
    user_vector_np = np.array(user_vector).reshape(1, -1)
    similar_users = get_KMeans_recommandations(user_vector_np)
    #print(f"Categorii recomandate pentru userul {user_id}:")
    #print(generate_category_recommendations(user_id, similar_users))
    return similar_users
def get_recommendations_for_user(user_id):
    # print("KNN Recommendations:")
    KnnRecomandations = get_knn_recommendations(user_id)
   # print("KMeans Recommendations:")
    KMeans=get_kmeans_recommendations(user_id)
    #print(KnnRecomandations)
   # print(KMeans)
    result=generate_category_recommendations(user_id, KnnRecomandations)
    generate_category_recommendations(user_id, KMeans)
    for category in generate_category_recommendations(user_id, KMeans):
        # if category not in result:
        result.append(category)
    return result

def clean_val(val):
    """Curăță valorile de tip string ($1,234.50) și le convertește în float."""
    if isinstance(val, str):
        return float(val.replace('$', '').replace(',', ''))
    return float(val)

def clean_val(val):
    """Curăță valorile string ($1,234.50) și le convertește în float."""
    if isinstance(val, str):
        return float(val.replace('$', '').replace(',', ''))
    return float(val)

def get_user_profile_csv(user_id, users_path=users_data_location, trans_path=payments_data_location):
    # 1. Încărcăm datele utilizatorului
    users_df = pd.read_csv(users_path)
    user_row = users_df[users_df['id'] == user_id]
    
    if user_row.empty:
        return None
    
    user = user_row.iloc[0]

    # 2. Formăm profilul de bază din datele demografice
    profile = {
        "current_age": int(user['current_age']),
        "yearly_income": clean_val(user['yearly_income']),
        "total_debt": clean_val(user['total_debt']),
        "credit_score": int(user['credit_score'])
    }

    # 3. Încărcăm tranzacțiile deja categorisite
    # Citim doar client_id, amount și category pentru eficiență
    trans_df = pd.read_csv(trans_path, usecols=['client_id', 'amount', 'category'])
    client_trans = trans_df[trans_df['client_id'] == user_id]

    # 4. Agregăm cheltuielile pe categorii
    if not client_trans.empty:
        # Grupăm după coloana 'category' și sumăm coloana 'amount'
        # (Nu mai e nevoie de clean_val aici dacă amount e deja numeric în fișier)
        category_sums = client_trans.groupby('category')['amount'].sum()

        # Adăugăm fiecare categorie ca o cheie în dicționarul profile
        for category, total in category_sums.items():
            profile[category] = float(total)

    return profile
#print(get_recommendations_for_user(37))
def temp():
    import pandas as pd
    import numpy as np
    import os

    # 1. Încărcare date
    file_path = 'RecomandationSystem/data/testData.txt'
    real_df_raw = pd.read_csv(file_path, sep=';', header=None, names=['id', 'c1', 'c2', 'c3'])
    gt_dict = real_df_raw.set_index('id').T.to_dict('list')
    
    # Avem nevoie de lista tuturor categoriilor posibile pentru a identifica itemii "negativi"
    all_categories = pd.read_csv('RecomandationSystem/data/transactions_data_categorized.csv')['category'].unique().tolist()

    def calculate_full_metrics(algo_func, name):
        results = {
            'precision': [], 'recall': [], 'mrr': [], 'auc': []
        }
        
        user_ids = list(gt_dict.keys())[:100]
        
        for uid in user_ids:
            real_cats = [str(c).strip() for c in gt_dict[uid]]
            try:
                pred_cats = algo_func(uid)
                actual_set = set(real_cats)
                pred_set = set(pred_cats[:3])
                
                hits = len(pred_set & actual_set)
                results['precision'].append(hits / 3.0)
                results['recall'].append(hits / len(actual_set))
                
                # --- CALCUL MRR ---
                rr = 0
                for i, p in enumerate(pred_cats[:3]):
                    if p in actual_set:
                        rr = 1 / (i + 1)
                        break
                results['mrr'].append(rr)

                # --- CALCUL AUC (Simplified for RecSys) ---
                # Formula: (Nr. perechi corect ordonate) / (Total perechi posibil relevante vs irelevante)
                # Un item relevant e mai "sus" decât unul irelevant?
                negative_items = list(set(all_categories) - actual_set)
                
                auc_user = 0
                if actual_set and negative_items:
                    found_relevant = 0
                    for rel_item in actual_set:
                        # Verificăm poziția în lista extinsă returnată de algoritm
                        # (Presupunem că algoritmul poate returna o listă mai lungă de scoruri)
                        try:
                            rank_rel = pred_cats.index(rel_item)
                        except ValueError:
                            rank_rel = 999 # Penalizare dacă nu e în listă
                        
                        # Luăm un eșantion de itemi negativi pentru viteză
                        neg_samples = np.random.choice(negative_items, min(20, len(negative_items)), replace=False)
                        for neg_item in neg_samples:
                            try:
                                rank_neg = pred_cats.index(neg_item)
                            except ValueError:
                                rank_neg = 1000
                            
                            if rank_rel < rank_neg:
                                auc_user += 1
                        found_relevant += len(neg_samples)
                    
                    results['auc'].append(auc_user / found_relevant if found_relevant > 0 else 0)

            except: continue

        print(f"\n" + "="*50)
        print(f"RAPORT FINAL LICENȚĂ: {name}")
        print(f"="*50)
        print(f"Precision@3: {np.mean(results['precision']):.4f}")
        print(f"Recall@3:    {np.mean(results['recall']):.4f}")
        print(f"MRR:         {np.mean(results['mrr']):.4f}")
        print(f"AUC:         {np.mean(results['auc']):.4f} (Capacitate de discriminare)")

    # Wrapper-e (Knn și KMeans)
    calculate_full_metrics(lambda u: generate_category_recommendations(u, get_knn_recommendations(u)), "k-NN")
    calculate_full_metrics(lambda u: generate_category_recommendations(u, get_kmeans_recommendations(u)), "k-Means")

# Apelează funcția
# temp()
#print_neighbor_spending_from_df([i for i in range(100,160)])
# populate_payment_types()
# populate_with_users_and_cards()
# insert_test_payments(1)
temp()
#get_recommendations_for_user(1)
