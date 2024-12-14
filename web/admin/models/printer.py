from datetime import datetime

class PrinterStatus:
    IDLE = 'idle'
    PRINTING = 'printing'
    PAUSED = 'paused'
    ERROR = 'error'
    OFFLINE = 'offline'

class Printer:
    def __init__(self, id, name, model=None):
        self.id = id
        self.name = name
        self.model = model
        self.status = PrinterStatus.IDLE
        self.current_job = None
        self.temperature = {'bed': 0, 'nozzle': 0}
        self.progress = 0
        self.last_update = datetime.now()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model,
            'status': self.status,
            'temperature': self.temperature,
            'progress': self.progress,
            'last_update': self.last_update.isoformat()
        }

class PrintJob:
    def __init__(self, id, name, file_path, user_id):
        self.id = id
        self.name = name
        self.file_path = file_path
        self.user_id = user_id
        self.started_at = None
        self.completed_at = None
        self.status = 'pending'
        self.progress = 0

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'progress': self.progress,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
