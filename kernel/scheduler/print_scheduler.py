import threading
from queue import PriorityQueue
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PrintJob:
    device_id: str
    gcode_file: str
    priority: int
    created_at: datetime
    
    def __lt__(self, other):
        return self.priority < other.priority

class PrintScheduler:
    def __init__(self):
        self.job_queue = PriorityQueue()
        self.active_jobs: Dict[str, PrintJob] = {}
        self.running = False
        self.thread = None
        
    def add_job(self, device_id: str, gcode_file: str, priority: int = 1):
        """Fügt einen neuen Druckauftrag zur Queue hinzu"""
        job = PrintJob(
            device_id=device_id,
            gcode_file=gcode_file,
            priority=priority,
            created_at=datetime.now()
        )
        self.job_queue.put(job)
        
    def start(self):
        """Startet den Scheduler"""
        self.running = True
        self.thread = threading.Thread(target=self._process_queue)
        self.thread.start()
        
    def stop(self):
        """Stoppt den Scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
            
    def _process_queue(self):
        """Verarbeitet die Job-Queue"""
        while self.running:
            if not self.job_queue.empty():
                job = self.job_queue.get()
                if job.device_id not in self.active_jobs:
                    self.active_jobs[job.device_id] = job
                    self._start_print_job(job)
                else:
                    # Wenn der Drucker beschäftigt ist, Job wieder in Queue
                    self.job_queue.put(job)
            threading.Event().wait(1)  # Kleine Pause
            
    def _start_print_job(self, job: PrintJob):
        """Startet einen Druckauftrag"""
        # TODO: Implementiere tatsächlichen Druckstart
        pass
        
    def get_queue_status(self) -> List[PrintJob]:
        """Gibt den aktuellen Status der Queue zurück"""
        return list(self.job_queue.queue)
