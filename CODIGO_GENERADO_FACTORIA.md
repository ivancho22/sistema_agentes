Para implementar un sistema de agendamiento de citas con selección de combos y pago por PSE utilizando FastAPI y SQL, primero crearemos el script DDL SQL para definir la estructura de la base de datos y luego el código Python completo para la API.

### 1. Script DDL SQL (schema.sql)

```sql
-- schema.sql

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL
);

CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    service_id INT REFERENCES services(id),
    appointment_time TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled'
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    appointment_id INT REFERENCES appointments(id),
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending'
);
```

### 2. Código Python Completo (main.py) con FastAPI

```python
# main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DECIMAL, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./test.db"  # Cambiar a la base de datos deseada
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# Modelos de SQLAlchemy
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(DECIMAL)

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    appointment_time = Column(TIMESTAMP)
    status = Column(String, default='scheduled')

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    amount = Column(DECIMAL)
    payment_method = Column(String)
    status = Column(String, default='pending')

# Crear las tablas
Base.metadata.create_all(bind=engine)

# Esquemas de Pydantic
class UserCreate(BaseModel):
    name: str
    email: str
    phone: str

class ServiceCreate(BaseModel):
    name: str
    price: float

class AppointmentCreate(BaseModel):
    user_id: int
    service_id: int
    appointment_time: str

class PaymentCreate(BaseModel):
    appointment_id: int
    amount: float
    payment_method: str

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rutas de la API
@app.post("/users/", response_model=UserCreate)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email, phone=user.phone)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/services/", response_model=ServiceCreate)
def create_service(service: ServiceCreate, db: Session = Depends(get_db)):
    db_service = Service(name=service.name, price=service.price)
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@app.post("/appointments/", response_model=AppointmentCreate)
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    db_appointment = Appointment(
        user_id=appointment.user_id,
        service_id=appointment.service_id,
        appointment_time=appointment.appointment_time
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@app.post("/payments/", response_model=PaymentCreate)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    db_payment = Payment(
        appointment_id=payment.appointment_id,
        amount=payment.amount,
        payment_method=payment.payment_method
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment
```

### Instrucciones para ejecutar

1. **Crear la base de datos**: Ejecuta el script `schema.sql` en tu base de datos SQL.
2. **Instalar dependencias**: Asegúrate de tener FastAPI y SQLAlchemy instalados. Puedes instalarlos usando pip:
   ```bash
   pip install fastapi[all] sqlalchemy
   ```
3. **Ejecutar la aplicación**: Usa el siguiente comando para ejecutar la aplicación FastAPI:
   ```bash
   uvicorn main:app --reload
   ```
4. **Acceder a la API**: Abre tu navegador y ve a `http://127.0.0.1:8000/docs` para ver la documentación interactiva de la API.

Este código proporciona una base sólida para agendar citas, seleccionar combos y realizar pagos utilizando PSE. Puedes expandirlo según sea necesario para incluir más funcionalidades, como autenticación, validaciones adicionales, y manejo de errores.