from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import SessionLocal
from .. import models, schemas

router = APIRouter(
    prefix="/printers",
    tags=["printers"]
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.Printer])
def get_printers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    printers = db.query(models.Printer).offset(skip).limit(limit).all()
    return printers

@router.post("/", response_model=schemas.Printer)
def create_printer(printer: schemas.PrinterCreate, db: Session = Depends(get_db)):
    db_printer = models.Printer(**printer.dict())
    db.add(db_printer)
    db.commit()
    db.refresh(db_printer)
    return db_printer

@router.get("/{printer_id}", response_model=schemas.Printer)
def get_printer(printer_id: int, db: Session = Depends(get_db)):
    printer = db.query(models.Printer).filter(models.Printer.id == printer_id).first()
    if printer is None:
        raise HTTPException(status_code=404, detail="Drucker nicht gefunden")
    return printer
