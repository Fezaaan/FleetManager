import cv2
import json
import numpy as np

# Globale Variablen
points = []  # Aktuelle Punkte für einen Parkplatz
all_parkings = []  # Liste aller gespeicherten Parkplätze
global_coordinates = {}  # Globale Fensterkoordinaten
current_parking_id = ""  # Zwischenspeicher für die Eingabe der Parkplatz-ID
selected_parking = None  # Für das Löschen eines Parkplatzes

# Funktion zur Initialisierung der JSON-Datei
def initialize_json():
    global global_coordinates, all_parkings
    try:
        with open("all_parkings.json", "r") as json_file:
            data = json.load(json_file)
            global_coordinates = data.get("global_coordinates", calculate_global_coordinates(frame))
            all_parkings = data.get("parkings", [])
            print("JSON-Datei erfolgreich geladen.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("JSON-Datei nicht gefunden oder leer. Erstelle Standardstruktur...")
        with open("all_parkings.json", "w") as json_file:
            default_structure = {
                "global_coordinates": calculate_global_coordinates(frame),
                "parkings": []
            }
            json.dump(default_structure, json_file, indent=4)
        global_coordinates = calculate_global_coordinates(frame)
        all_parkings = []

# Funktion zur Berechnung der globalen Fensterkoordinaten
def calculate_global_coordinates(frame):
    """Berechnet die globalen Fensterkoordinaten (ul, ur, ol, or) basierend auf der Bildgröße."""
    h, w = frame.shape[:2]  # Höhe und Breite des Bildes
    return {
        "ul": [0, h],         # Unten links
        "ur": [w, h],         # Unten rechts
        "ol": [0, 0],         # Oben links
        "or": [w, 0]          # Oben rechts
    }

# Funktion zur Verarbeitung von Mausaktionen
def mouse_callback(event, x, y, flags, param):
    global points, selected_parking, all_parkings, frame
    if event == cv2.EVENT_LBUTTONDOWN:  # Linksklick
        points.append((x, y))  # Punkt zur Liste hinzufügen
        print(f"Klick-Koordinaten: ({x}, {y})")  # Koordinaten in der Konsole ausgeben
    elif event == cv2.EVENT_RBUTTONDOWN:  # Rechtsklick
        for parking in all_parkings:
            area = np.array(parking["coordinates"], np.int32)
            if cv2.pointPolygonTest(area, (x, y), False) >= 0:
                selected_parking = parking
                all_parkings.remove(parking)
                print(f"Parkplatz-ID {parking['id']} wurde entfernt.")
                update_json()
                reload_parkings(frame)
                break

# Fenster und Mouse-Callback initialisieren
cv2.namedWindow('Image', cv2.WINDOW_NORMAL)
cv2.setMouseCallback('Image', mouse_callback)

# Bild öffnen
image_path = 'screenshot_0.jpg'  # Pfad zu deinem Bild
frame = cv2.imread(image_path)

if frame is None:
    print("Bild konnte nicht geladen werden. Bitte überprüfe den Pfad.")
    exit()

# Vorhandene Parkplätze aus JSON laden
def reload_parkings(frame):
    global all_parkings
    try:
        with open("all_parkings.json", "r") as json_file:
            data = json.load(json_file)
            all_parkings = data.get("parkings", [])
            print("JSON-Datei neu geladen.")
            # Entferne alle Linien vom ursprünglichen Frame
            frame[:] = cv2.imread(image_path)
    except FileNotFoundError:
        print("JSON-Datei nicht gefunden. Eine neue Datei wird erstellt.")

# Funktion zum Aktualisieren der JSON-Datei
def update_json():
    with open("all_parkings.json", "w") as json_file:
        json.dump({
            "global_coordinates": global_coordinates,
            "parkings": all_parkings
        }, json_file, indent=4)
    print("JSON-Datei wurde aktualisiert.")

# JSON initialisieren
initialize_json()

# Hauptschleife
while True:
    # Kopiere das Bild, damit Punkte hinzugefügt werden können
    display_frame = frame.copy()

    # Bestehende Parkplätze zeichnen
    for parking in all_parkings:
        area = np.array(parking["coordinates"], np.int32)
        cv2.polylines(display_frame, [area], True, (0, 255, 0), 2)
        cv2.putText(display_frame, parking["id"], tuple(parking["coordinates"][0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Zeichne alle Punkte aus der Liste
    for point in points:
        cv2.circle(display_frame, point, 5, (255, 0, 0), -1)  # Blauer Punkt

    # Zeichne ein Rechteck, wenn genau 4 Punkte vorhanden sind
    if len(points) == 4:
        cv2.polylines(display_frame, [np.array(points, np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)

        # Zeige grafische Eingabeaufforderung
        cv2.putText(display_frame, "Enter Parking ID:", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(display_frame, current_parking_id, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Zeige die Tastenanweisungen oben rechts im Frame
    instructions = [
        "Linksklick: Punkt setzen",
        "Rechtsklick: Parkplatz entfernen",
        "Enter: Parkplatz-ID speichern",
        "Z: Letzten Punkt entfernen",
        "Q: Beenden"
    ]

    x_offset = display_frame.shape[1] - 300
    y_offset = 20
    for i, text in enumerate(instructions):
        cv2.putText(display_frame, text, (x_offset, y_offset + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # Bild anzeigen
    cv2.imshow("Image", display_frame)

    # Warte auf Benutzereingabe
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):  # Taste Q für Beenden
        # Programm beenden und alle Parkplätze speichern
        if all_parkings:
            update_json()
        else:
            print("Keine Parkplätze zum Speichern gefunden.")
        break
    elif key == ord('z') and points:  # Taste Z und es gibt Punkte
        removed_point = points.pop()  # Letzten Punkt entfernen
        print(f"Letzter Punkt gelöscht: {removed_point}")
    elif len(points) == 4:  # Eingabe der Parkplatz-ID
        if key == 13:  # Enter-Taste
            if current_parking_id.strip() == "":
                print("Parkplatz-ID darf nicht leer sein.")
            else:
                parking_data = {
                    "id": current_parking_id,
                    "coordinates": points,
                    "car": False,
                    "license_plate": "",
                }
                all_parkings.append(parking_data)  # Parkplatz zur Liste hinzufügen
                print(f"Parkplatz-ID {current_parking_id} mit Koordinaten {points} wurde gespeichert.")

                # Rechteck dauerhaft zeichnen und Punkte zurücksetzen
                cv2.polylines(frame, [np.array(points, np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)
                points = []  # Punkte zurücksetzen
                current_parking_id = ""  # ID zurücksetzen

                # JSON-Datei direkt aktualisieren
                update_json()
        elif 48 <= key <= 57 or 65 <= key <= 90 or 97 <= key <= 122:  # Alphanumerische Zeichen
            current_parking_id += chr(key)  # Zeichen zur ID hinzufügen
        elif key in (8, 127):  # Backspace auf verschiedenen Systemen
            current_parking_id = current_parking_id[:-1]  # Letztes Zeichen entfernen

# Fenster schließen
cv2.destroyAllWindows()
