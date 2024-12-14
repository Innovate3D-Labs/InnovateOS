#!/usr/bin/env python3
import os
import time
import json
import psutil
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading

class SystemMonitor:
    def __init__(self):
        self.db_path = Path("/var/lib/innovate/monitoring.db")
        self.log_dir = Path("/var/log/innovate")
        self.logger = self._setup_logging()
        self.metrics = {}
        self.alert_thresholds = self._load_thresholds()
        self.running = True
        
        # Initialisiere Datenbank
        self._init_database()
        
    def _setup_logging(self):
        logger = logging.getLogger('SystemMonitor')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('/var/log/innovate/monitor.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        return logger
        
    def _load_thresholds(self) -> Dict:
        """Lädt Schwellenwerte aus der Konfiguration"""
        try:
            with open("/etc/innovate/monitoring.conf", "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Schwellenwerte: {e}")
            return {
                'cpu_percent': 90,
                'memory_percent': 90,
                'disk_percent': 90,
                'temperature': 80
            }
            
    def _init_database(self):
        """Initialisiert die SQLite-Datenbank"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Metrics-Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    timestamp DATETIME,
                    metric_type TEXT,
                    value REAL,
                    PRIMARY KEY (timestamp, metric_type)
                )
            ''')
            
            # Alerts-Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    timestamp DATETIME PRIMARY KEY,
                    alert_type TEXT,
                    message TEXT,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Datenbankfehler: {e}")
            
    def collect_metrics(self):
        """Sammelt Systemmetriken"""
        try:
            self.metrics = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'network': {
                    'bytes_sent': psutil.net_io_counters().bytes_sent,
                    'bytes_recv': psutil.net_io_counters().bytes_recv
                },
                'temperature': self._get_temperature(),
                'processes': len(psutil.pids()),
                'timestamp': datetime.now().isoformat()
            }
            
            # Speichere in Datenbank
            self._store_metrics(self.metrics)
            
            # Prüfe Schwellenwerte
            self._check_thresholds(self.metrics)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Sammeln der Metriken: {e}")
            
    def _get_temperature(self) -> Optional[float]:
        """Liest CPU-Temperatur"""
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                return max(temp.current for temp in temps['coretemp'])
            return None
        except Exception:
            return None
            
    def _store_metrics(self, metrics: Dict):
        """Speichert Metriken in der Datenbank"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now()
            for metric_type, value in metrics.items():
                if isinstance(value, (int, float)):
                    cursor.execute(
                        'INSERT INTO metrics (timestamp, metric_type, value) VALUES (?, ?, ?)',
                        (timestamp, metric_type, value)
                    )
                    
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Metriken: {e}")
            
    def _check_thresholds(self, metrics: Dict):
        """Prüft Schwellenwerte und erzeugt Alarme"""
        for metric, value in metrics.items():
            if metric in self.alert_thresholds:
                threshold = self.alert_thresholds[metric]
                if isinstance(value, (int, float)) and value > threshold:
                    self._create_alert(
                        f"{metric}_high",
                        f"{metric} über Schwellenwert: {value:.1f}% (Max: {threshold}%)"
                    )
                    
    def _create_alert(self, alert_type: str, message: str):
        """Erstellt einen neuen Alarm"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO alerts (timestamp, alert_type, message) VALUES (?, ?, ?)',
                (datetime.now(), alert_type, message)
            )
            
            conn.commit()
            conn.close()
            
            self.logger.warning(f"Alert: {message}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des Alarms: {e}")
            
    def get_metrics(self, hours: int = 24) -> List[Dict]:
        """Holt historische Metriken"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = datetime.now() - timedelta(hours=hours)
            cursor.execute(
                'SELECT * FROM metrics WHERE timestamp > ? ORDER BY timestamp',
                (since,)
            )
            
            metrics = []
            for row in cursor.fetchall():
                metrics.append({
                    'timestamp': row[0],
                    'metric_type': row[1],
                    'value': row[2]
                })
                
            conn.close()
            return metrics
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Metriken: {e}")
            return []
            
    def get_alerts(self, resolved: bool = False) -> List[Dict]:
        """Holt aktive oder gelöste Alarme"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM alerts WHERE resolved = ? ORDER BY timestamp DESC',
                (resolved,)
            )
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'timestamp': row[0],
                    'type': row[1],
                    'message': row[2]
                })
                
            conn.close()
            return alerts
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Alarme: {e}")
            return []
            
    def cleanup_old_data(self, days: int = 30):
        """Entfernt alte Metriken und gelöste Alarme"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cleanup_date = datetime.now() - timedelta(days=days)
            
            # Lösche alte Metriken
            cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cleanup_date,))
            
            # Lösche alte, gelöste Alarme
            cursor.execute(
                'DELETE FROM alerts WHERE timestamp < ? AND resolved = TRUE',
                (cleanup_date,)
            )
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Alte Daten gelöscht (älter als {days} Tage)")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aufräumen: {e}")
            
    def run(self):
        """Hauptschleife"""
        self.logger.info("System-Monitor gestartet")
        
        cleanup_thread = threading.Thread(target=self._cleanup_thread)
        cleanup_thread.start()
        
        try:
            while self.running:
                self.collect_metrics()
                time.sleep(60)  # Sammle Metriken jede Minute
                
        except KeyboardInterrupt:
            self.running = False
            cleanup_thread.join()
            self.logger.info("System-Monitor beendet")
            
    def _cleanup_thread(self):
        """Thread für regelmäßiges Aufräumen"""
        while self.running:
            self.cleanup_old_data()
            time.sleep(86400)  # Einmal täglich aufräumen
            
if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.run()
