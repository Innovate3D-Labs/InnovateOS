# InnovateOS Windows Installer

Ein benutzerfreundlicher Installer für InnovateOS, der die SD-Karte automatisch vorbereitet.

## Features

- Grafische Benutzeroberfläche
- Automatische Erkennung von SD-Karten
- Sichere Installation des Betriebssystems
- Grundkonfiguration des Systems
- Verifizierung der Installation

## Voraussetzungen

- Windows 10/11
- Python 3.9 oder höher
- Administrator-Rechte
- SD-Karte (min. 8GB)

## Installation

1. Installiere die benötigten Python-Pakete:
```bash
cd installer
pip install -r requirements.txt
```

2. Starte den Installer:
```bash
python main.py
```

Eine detaillierte Anleitung zur Verwendung des Installers findest du in der [INSTALLER.md](INSTALLER.md).

## Entwicklung

### Projektstruktur

```
installer/
├── main.py              # Hauptanwendung
├── requirements.txt     # Python-Abhängigkeiten
├── README.md           # Dokumentation
├── ui/                 # Benutzeroberfläche
│   ├── main_window.py  # Hauptfenster
│   └── pages/         # Einzelne Seiten
├── utils/              # Hilfsfunktionen
│   ├── installer.py    # Installations-Logik
│   └── logger.py       # Logging-Funktionen
└── resources/          # Ressourcen (Icons, etc.)
```

### Build

Um eine ausführbare Datei zu erstellen:

```bash
pyinstaller --onefile --windowed main.py
```

## Sicherheit

- Backup-Option vor der Installation
- Verifizierung nach der Installation
- Sichere Behandlung von Systemrechten

## Lizenz

Dieses Projekt ist Teil von InnovateOS und unter der gleichen Lizenz verfügbar.
