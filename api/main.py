from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel

app = FastAPI(title="InnovateOS API")

# CORS-Konfiguration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = "your-secret-key"  # In Produktion aus Umgebungsvariable laden
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class SystemStatus(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    temperature: Optional[float]
    uptime: int

class PrinterStatus(BaseModel):
    id: str
    name: str
    status: str
    temperature: dict
    progress: Optional[float]

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # TODO: Implementiere echte Benutzerauthentifizierung
    if form_data.username == "admin" and form_data.password == "password":
        access_token = create_access_token(
            data={"sub": form_data.username}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=400,
        detail="Incorrect username or password"
    )

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
        return username
    except jwt.JWTError:
        raise HTTPException(status_code=401)

# System-Endpunkte
@app.get("/system/status", response_model=SystemStatus)
async def get_system_status(_: str = Depends(get_current_user)):
    from system.monitoring.system_monitor import SystemMonitor
    monitor = SystemMonitor()
    metrics = monitor.metrics
    return SystemStatus(
        cpu_usage=metrics['cpu_percent'],
        memory_usage=metrics['memory_percent'],
        disk_usage=metrics['disk_percent'],
        temperature=metrics.get('temperature'),
        uptime=int(metrics['uptime'])
    )

@app.get("/system/logs")
async def get_system_logs(
    log_type: str,
    lines: int = 100,
    _: str = Depends(get_current_user)
):
    import os
    log_files = {
        'system': '/var/log/innovate_init.log',
        'network': '/var/log/innovate_network.log',
        'update': '/var/log/innovate_update.log'
    }
    
    if log_type not in log_files:
        raise HTTPException(status_code=400, detail="Invalid log type")
        
    try:
        with open(log_files[log_type], 'r') as f:
            return {'logs': f.readlines()[-lines:]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Drucker-Endpunkte
@app.get("/printers", response_model=List[PrinterStatus])
async def get_printers(_: str = Depends(get_current_user)):
    from kernel.core.kernel import InnovateKernel
    kernel = InnovateKernel()
    return [
        PrinterStatus(
            id=printer.id,
            name=printer.name,
            status=printer.status,
            temperature=printer.temperature,
            progress=printer.progress if printer.status == "printing" else None
        )
        for printer in kernel.devices.values()
    ]

@app.post("/printers/{printer_id}/command")
async def send_printer_command(
    printer_id: str,
    command: str,
    _: str = Depends(get_current_user)
):
    from kernel.core.kernel import InnovateKernel
    kernel = InnovateKernel()
    printer = kernel.get_device(printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    try:
        result = printer.send_command(command)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Backup-Endpunkte
@app.post("/backup/create")
async def create_backup(
    name: Optional[str] = None,
    _: str = Depends(get_current_user)
):
    from system.backup.backup_manager import BackupManager
    manager = BackupManager()
    success = manager.create_backup(name)
    if success:
        return {"status": "success", "name": name}
    raise HTTPException(status_code=500, detail="Backup failed")

@app.post("/backup/restore/{backup_name}")
async def restore_backup(
    backup_name: str,
    _: str = Depends(get_current_user)
):
    from system.backup.backup_manager import BackupManager
    manager = BackupManager()
    success = manager.restore_backup(backup_name)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Restore failed")

# Update-Endpunkte
@app.get("/updates/check")
async def check_updates(_: str = Depends(get_current_user)):
    from system.update.system_updater import SystemUpdater
    updater = SystemUpdater()
    update_info = updater.check_for_updates()
    return {"updates_available": bool(update_info), "info": update_info}

@app.post("/updates/apply")
async def apply_update(_: str = Depends(get_current_user)):
    from system.update.system_updater import SystemUpdater
    updater = SystemUpdater()
    update_info = updater.check_for_updates()
    if not update_info:
        raise HTTPException(status_code=404, detail="No updates available")
        
    package_path = updater.download_update(update_info)
    if not package_path:
        raise HTTPException(status_code=500, detail="Update download failed")
        
    success = updater.apply_update(package_path)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Update failed")
