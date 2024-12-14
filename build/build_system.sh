#!/bin/bash

# Build-Skript für InnovateOS

set -e

# Konfiguration
WORKDIR="$(pwd)/build_tmp"
OUTPUT_DIR="$(pwd)/output"
ROOTFS_SIZE="1G"

# Abhängigkeiten prüfen
check_dependencies() {
    local deps=(debootstrap parted dosfstools e2fsprogs)
    for dep in "${deps[@]}"; do
        if ! command -v $dep &> /dev/null; then
            echo "Fehler: $dep ist nicht installiert"
            exit 1
        fi
    done
}

# Arbeitsverzeichnis vorbereiten
prepare_directories() {
    rm -rf "$WORKDIR"
    mkdir -p "$WORKDIR"
    mkdir -p "$OUTPUT_DIR"
}

# Basis-System erstellen
create_rootfs() {
    echo "Erstelle Basis-System..."
    debootstrap --arch=amd64 --variant=minbase bullseye "$WORKDIR/rootfs"
    
    # Grundlegende Konfiguration
    cat > "$WORKDIR/rootfs/etc/fstab" << EOF
/dev/root / ext4 defaults 0 1
proc /proc proc defaults 0 0
sysfs /sys sysfs defaults 0 0
devpts /dev/pts devpts defaults 0 0
tmpfs /run tmpfs defaults 0 0
EOF
    
    # Hostname setzen
    echo "innovate-3d" > "$WORKDIR/rootfs/etc/hostname"
    
    # Netzwerkkonfiguration
    cat > "$WORKDIR/rootfs/etc/network/interfaces" << EOF
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp
EOF
}

# InnovateOS-spezifische Dateien installieren
install_innovate_files() {
    echo "Installiere InnovateOS-Dateien..."
    
    # Verzeichnisstruktur erstellen
    mkdir -p "$WORKDIR/rootfs/usr/local/bin"
    mkdir -p "$WORKDIR/rootfs/etc/innovate"
    mkdir -p "$WORKDIR/rootfs/var/lib/innovate"
    
    # Kopiere Systemdateien
    cp ../system/init/innovate_init.py "$WORKDIR/rootfs/usr/local/bin/"
    cp ../system/config/system.conf "$WORKDIR/rootfs/etc/innovate/"
    
    # Setze Berechtigungen
    chmod +x "$WORKDIR/rootfs/usr/local/bin/innovate_init.py"
}

# Image erstellen
create_image() {
    echo "Erstelle System-Image..."
    
    # Image-Datei erstellen
    dd if=/dev/zero of="$OUTPUT_DIR/innovate_os.img" bs=1 count=0 seek=$ROOTFS_SIZE
    
    # Partitionierung
    parted "$OUTPUT_DIR/innovate_os.img" mklabel msdos
    parted "$OUTPUT_DIR/innovate_os.img" mkpart primary ext4 1MiB 100%
    
    # Formatierung
    LOOP_DEVICE=$(losetup -f --show "$OUTPUT_DIR/innovate_os.img")
    mkfs.ext4 "${LOOP_DEVICE}p1"
    
    # Mount und Kopieren
    mkdir -p "$WORKDIR/mnt"
    mount "${LOOP_DEVICE}p1" "$WORKDIR/mnt"
    cp -a "$WORKDIR/rootfs/." "$WORKDIR/mnt/"
    sync
    umount "$WORKDIR/mnt"
    losetup -d "$LOOP_DEVICE"
}

# Aufräumen
cleanup() {
    echo "Räume auf..."
    rm -rf "$WORKDIR"
}

# Hauptprozess
main() {
    echo "Starte Build-Prozess für InnovateOS..."
    
    check_dependencies
    prepare_directories
    create_rootfs
    install_innovate_files
    create_image
    cleanup
    
    echo "Build erfolgreich abgeschlossen!"
    echo "Image befindet sich in: $OUTPUT_DIR/innovate_os.img"
}

main "$@"
