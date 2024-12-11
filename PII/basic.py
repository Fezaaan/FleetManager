import cv2
import pandas as pd
import numpy as np
import json
from ultralytics import YOLO

# YOLOv8 Model laden
model = YOLO('yolov8s.pt')

# JSON-Datei laden
with open("all_parkings.json", "r") as json_file:
    data = json.load(json_file)

# Globale Koordinaten (falls benötigt)
global_coordinates = data["global_coordinates"]

# Parkplätze aus der JSON laden
parkings = data["parkings"]

# OpenCV-Fenster initialisieren
cv2.namedWindow('RGB')

# Videoquelle öffnen
cap = cv2.VideoCapture('parking1.mp4')

# COCO-Klassen laden
with open("coco.txt", "r") as my_file:
    class_list = my_file.read().split("\n")

# Screenshot Zähler
screenshot_counter = 0
paused = False  # Status für Pause

# Hauptschleife
while True:
    if not paused:
        ret, frame = cap.read()
        if not ret:
            break

        # Framegröße anpassen
        frame = cv2.resize(frame, (1020, 500))

        # YOLO-Vorhersagen
        results = model.predict(frame)
        detections = results[0].boxes.data
        px = pd.DataFrame(detections).astype("float")

        # Parkplätze überprüfen
        for parking in parkings:
            parking_id = parking["id"]
            area = parking["coordinates"]
            area_np = np.array(area, np.int32)  # In NumPy-Array konvertieren

            list_objects = []

            for index, row in px.iterrows():
                x1, y1, x2, y2 = map(int, row[:4])
                class_id = int(row[5])
                class_name = class_list[class_id]

                if 'car' in class_name:  # Nur Autos prüfen
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2

                    # Prüfen, ob das Auto im Parkplatz liegt
                    if cv2.pointPolygonTest(area_np, (cx, cy), False) >= 0:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)
                        list_objects.append(class_name)

            # Parkplatz einfärben basierend auf dem Status
            if len(list_objects) > 0:
                cv2.polylines(frame, [area_np], True, (0, 0, 255), 2)
                cv2.putText(frame, f"{parking_id}", tuple(area[0]), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1)
            else:
                cv2.polylines(frame, [area_np], True, (0, 255, 0), 2)
                cv2.putText(frame, f"{parking_id}", tuple(area[0]), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

    # Frame anzeigen
    cv2.imshow("RGB", frame)

    # Tasteneingaben verarbeiten
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):  # Taste 'q' zum Beenden
        break
    elif key == 32:  # Leertaste
        paused = not paused  # Pause-Status umschalten
    elif key == ord('s'):  # Taste 's' für Screenshot
        screenshot_filename = f"screenshot_{screenshot_counter}.jpg"
        cv2.imwrite(screenshot_filename, frame)  # Aktuelles Frame speichern
        print(f"Screenshot gespeichert: {screenshot_filename}")
        screenshot_counter += 1

# Ressourcen freigeben
cap.release()
cv2.destroyAllWindows()