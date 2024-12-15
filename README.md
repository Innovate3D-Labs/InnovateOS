# InnovateOS - Das moderne 3D-Drucker Betriebssystem

InnovateOS ist ein modernes, KI-gestütztes Betriebssystem für 3D-Drucker, das Benutzerfreundlichkeit, Sicherheit und Erweiterbarkeit in den Vordergrund stellt. Es bietet eine intuitive Weboberfläche zur Steuerung und Überwachung Ihres 3D-Druckers, zusammen mit fortschrittlichen Funktionen wie Fernzugriff, automatische Updates und Plugin-Unterstützung.

## Hauptfunktionen

### 🖨️ Druckersteuerung
- Intuitive Weboberfläche zur Druckersteuerung
- Echtzeit-Überwachung von Temperatur und Druckfortschritt
- Automatische Druckbett-Nivellierung
- Temperatur-Profile für verschiedene Materialien
- G-Code-Visualisierung und -Vorschau

### 🤖 KI & Automatisierung
- Echtzeit-Druckfehler-Erkennung mit maschinellem Lernen
- Automatische Qualitätsoptimierung
- Vorausschauende Wartung
- Selbstlernende Druckprofile
- Automatische G-Code-Optimierung

### 🔒 Sicherheit
- Umfassendes Benutzer- und Rechtesystem
- Zwei-Faktor-Authentifizierung
- Thermal Runaway Protection
- Automatische Backups
- Sichere API-Schlüssel-Verwaltung
- Verschlüsselte Kommunikation

### 🔌 Erweiterbarkeit
- Plugin-System für zusätzliche Funktionen
- Plugin-Marketplace mit automatischen Updates
- Anpassbare Benutzeroberfläche
- API für Drittanbieter-Integration
- Unterstützung für verschiedene Drucker-Firmware
- Benutzerdefinierte Makros und Skripte
- Dependency Management für Plugins

### 🔄 System
- Automatische System-Updates
- Backup und Wiederherstellung
- Leistungsüberwachung
- Fehlerprotokollierung
- Remote-Zugriff
- Cloud-Integration (in Entwicklung)

### 🌐 API & Integration
- RESTful API mit OpenAPI/Swagger Dokumentation
- WebSocket-Unterstützung für Echtzeit-Updates
- SDK für Python und JavaScript
- OctoPrint-Kompatibilität (geplant)
- IoT-Integration

## New Features in v1.3-Beta

### Enhanced AI Integration
- Live Feedback System for continuous model improvement
- Extended error detection capabilities
- Community-driven model training
- Real-time print quality monitoring

### Improved Plugin System
- Plugin Rating & Review System
- Automated plugin updates
- Plugin recommendations based on usage patterns
- Enhanced dependency management

### Advanced Material Management
- Comprehensive material profiles
- Temperature optimization
- Brand-specific settings
- Material usage tracking

### Community Features
- Feedback Portal for feature requests and bug reports
- Anonymous telemetry system (opt-in)
- Community-driven development
- Usage analytics for better feature prioritization

## Installation

### Windows

1. Lade den [Windows Installer](installer/) oder den [Release](https://github.com/Innovate3D-Labs/Innovateos-installer) herunter
2. Installiere die benötigten Python-Pakete:
```bash
cd installer
pip install -r requirements.txt
```

3. Starte den Installer:
```bash
python main.py
```

4. Folge den Anweisungen des Installers:
   - Wähle deine SD-Karte aus
   - Konfiguriere WLAN und Drucker
   - Warte auf den Abschluss der Installation

Eine detaillierte Anleitung findest du in der [Installer-Dokumentation](installer/INSTALLER.md).

### Linux (Manuell)

### Kompatible 3D-Drucker
InnovateOS wurde für folgende 3D-Drucker-Mainboards getestet:
- BTT SKR Mini E3 V2/V3
- BTT SKR V1.4/V2.0
- MKS Gen L V1/V2
- MKS Robin Nano V3
- Creality v4.2.7
- Prusa Mini/MK3S+ Einsy Board

### Voraussetzungen
- Kompatibles 3D-Drucker-Mainboard (siehe Liste oben)
- MicroSD-Karte (mindestens 8GB, Class 10 empfohlen)
- USB-zu-TTL Adapter für die initiale Installation
- Computer für die Firmware-Installation

### Firmware-Installation
1. Laden Sie das neueste InnovateOS-Image für Ihr Mainboard herunter:
   ```bash
   wget https://innovateos.org/download/[IHR_MAINBOARD].bin
   ```

2. Benennen Sie die Datei entsprechend Ihres Mainboards um:
   - BTT SKR: `firmware.bin`
   - MKS: `Robin_nano.bin`
   - Creality: `firmware.bin`
   - Prusa: `firmware.hex`

3. Kopieren Sie die Firmware auf eine leere MicroSD-Karte

4. Installation der Firmware:
   a) Schalten Sie den Drucker aus
   b) Stecken Sie die SD-Karte ein
   c) Schalten Sie den Drucker ein
   d) Warten Sie bis die Installation abgeschlossen ist (ca. 1-2 Minuten)
   e) Der Drucker startet automatisch neu

### Erste Einrichtung
1. Nach dem Neustart erstellt InnovateOS ein WLAN-Netzwerk:
   - Name: InnovateOS-[DRUCKER_ID]
   - Standardpasswort: innovate123

2. Verbinden Sie sich mit diesem WLAN-Netzwerk

3. Öffnen Sie im Browser:
   ```
   http://innovateos.local
   ```
   oder
   ```
   http://192.168.4.1
   ```

4. Folgen Sie dem Einrichtungsassistenten:
   - Wählen Sie Ihre Sprache
   - Konfigurieren Sie Ihr WLAN
   - Setzen Sie ein Administrator-Passwort
   - Kalibrieren Sie Ihren Drucker

### Sicherheitshinweise
- Ändern Sie unbedingt das Standard-WLAN-Passwort
- Führen Sie vor der Installation ein Backup Ihrer aktuellen Firmware durch
- Bei Problemen können Sie jederzeit die Original-Firmware wiederherstellen
- Stellen Sie sicher, dass Ihr Drucker während der Installation nicht bewegt wird

### Fehlerbehebung
Falls der Drucker nach der Installation nicht startet:
1. Formatieren Sie die SD-Karte neu (FAT32)
2. Laden Sie die Firmware erneut herunter
3. Wiederholen Sie die Installation
4. Falls das Problem bestehen bleibt, stellen Sie die Original-Firmware wieder her

## Konfiguration

### Drucker-Einrichtung
1. Öffnen Sie die Web-Oberfläche (http://innovateos.local)
2. Gehen Sie zu Einstellungen > Drucker
3. Wählen Sie Ihr Drucker-Modell oder konfigurieren Sie einen benutzerdefinierten Drucker
4. Folgen Sie dem Kalibrierungsassistenten

### Netzwerk-Einrichtung
1. Verbinden Sie sich mit dem WLAN "InnovateOS-Setup"
2. Öffnen Sie http://innovateos.local/setup
3. Konfigurieren Sie Ihre Netzwerkeinstellungen
4. Das System wird neu starten und im konfigurierten Netzwerk verfügbar sein

### Benutzer-Verwaltung
1. Der Standard-Administrator-Account ist:
   - Benutzer: admin
   - Passwort: innovate
2. Ändern Sie das Passwort nach dem ersten Login
3. Erstellen Sie weitere Benutzer nach Bedarf

## Entwicklung

### Voraussetzungen
- Python 3.9+
- Node.js 14+
- Git

### Setup Entwicklungsumgebung
```bash
# Repository klonen
git clone https://github.com/InnovateOS/InnovateOS.git
cd InnovateOS

# Python-Abhängigkeiten installieren
pip install -r requirements.txt

# Frontend-Abhängigkeiten installieren
cd web/admin
npm install
```

### Plugin-Entwicklung
1. Erstellen Sie ein neues Plugin:
   ```bash
   innovate-cli create-plugin mein-plugin
   ```

2. Entwickeln Sie Ihr Plugin:
   ```python
   from innovateos import Plugin

   class MeinPlugin(Plugin):
       def initialize(self):
           self.register_endpoint('/mein-plugin', self.handle_request)
   ```

3. Bauen Sie Ihr Plugin:
   ```bash
   innovate-cli build-plugin mein-plugin
   ```

Weitere Informationen finden Sie im [Plugin-Entwicklungsguide](docs/plugin_development.md).

### Tests ausführen
```bash
# API Tests
pytest tests/

# Plugin Tests
pytest tests/test_plugin_api.py

# KI-Modell Training
python system/ai/train_model.py
```

### API-Nutzung
```python
import requests

# Verbindung zur InnovateOS API
api = InnovateOSAPI('http://innovateos.local', 'API_KEY')

# Druckerstatus abrufen
status = api.get_printer_status()

# Druck starten
api.start_print('model.gcode')
```

## API-Dokumentation

Die vollständige API-Dokumentation finden Sie unter:
- [API Referenz](docs/api_reference.md)
- [OpenAPI Spezifikation](docs/openapi.yaml)
- [Interaktive API-Docs](https://innovateos.org/api-docs)

## Support

### Community
- [Forum](https://forum.innovateos.org)
- [Discord](https://discord.gg/innovateos)
- [Wiki](https://wiki.innovateos.org)
- [Bug Reports](https://github.com/InnovateOS/InnovateOS/issues)
- [Feature Requests](https://github.com/InnovateOS/InnovateOS/discussions)

### Probleme melden
- [GitHub Issues](https://github.com/InnovateOS/InnovateOS/issues)
- [Bug Tracker](https://bugs.innovateos.org)

### Kommerzieller Support
- [Support-Pakete](https://innovateos.org/support)
- [Unternehmenslizenzen](https://innovateos.org/enterprise)

## Lizenz

InnovateOS ist unter der GNU General Public License v3.0 lizenziert. Siehe [LICENSE](LICENSE) für Details.

## Mitwirken

Wir freuen uns über Beiträge! Bitte lesen Sie unsere [Contribution Guidelines](CONTRIBUTING.md) für Details.

## Roadmap

### Q1 2025
- [ ] KI-basierte Druckoptimierung
- [ ] Plugin-Marketplace Beta
- [ ] Mobile App

### Q2 2025
- [ ] Cloud-Integration
- [ ] Multi-Drucker-Management
- [ ] OctoPrint-Kompatibilität

### Q3 2025
- [ ] Erweitertes Slicing
- [ ] IoT-Integration
- [ ] Automatische Kalibrierung

### Q4 2025
- [ ] AR/VR Unterstützung
- [ ] Cluster-Druck
- [ ] Cloud-Backup

Test
