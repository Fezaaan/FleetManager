import cv2
import pandas as pd
import numpy as np
import json
import time
from ultralytics import YOLO
import asyncio
import uuid
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message

# YOLOv8 Model laden
model = YOLO('yolov8s.pt')

# Azure IoT Hub-Konfiguration
CONNECTION_STRING = "HostName=ProjektLabor.azure-devices.net;DeviceId=OnlineSimulator;SharedAccessKey=Lfp1qcai6gyHk1XTGMC3HO2O0lmB7kUy4eajDG+/Ajw="
MQTT_TOPIC_PUBLISH = "devices/OnlineSimulator/messages/events/"

# JSON-Datei laden
with open("all_parkings.json", "r") as json_file:
    data = json.load(json_file)

global_coordinates = data["global_coordinates"]
parkings = data["parkings"]

# COCO-Klassen laden
with open("coco.txt", "r") as my_file:
    class_list = my_file.read().split("\n")

# Screenshot Zähler
screenshot_counter = 0
paused = False

async def send_to_azure(payload):
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    await client.connect()
    try:
        message = Message(payload)
        message.message_id = uuid.uuid4()
        message.content_encoding = "utf-8"
        message.content_type = "application/json"
        await client.send_message(message)
        print("Nachricht erfolgreich an Azure IoT Hub gesendet.")
    except Exception as ex:
        print(f"Fehler beim Senden der Nachricht an Azure IoT Hub: {ex}")
    finally:
        await client.shutdown()

# Funktion zur Aktualisierung der JSON-Datei und Senden an Azure
async def update_json():
    with open("all_parkings.json", "w") as json_file:
        json.dump({
            "global_coordinates": global_coordinates,
            "parkings": parkings
        }, json_file, indent=4)
    print("JSON-Datei wurde aktualisiert.")

    with open("all_parkings.json", "r") as json_file:
        data = json.load(json_file)
        data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        payload = json.dumps(data)
        print(f"Sende JSON-Daten an Azure: {payload}")
        await send_to_azure(payload)

# OpenCV-Fenster initialisieren
cv2.namedWindow('RGB')
cap = cv2.VideoCapture("parking1.mp4")

# Hauptschleife
async def main():
    global paused, screenshot_counter
    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (1020, 500))

            # YOLO-Vorhersagen
            results = model.predict(frame)
            detections = results[0].boxes.data
            px = pd.DataFrame(detections).astype("float")

            # Parkplätze überprüfen
            for parking in parkings:
                parking_id = parking["id"]
                area = parking["coordinates"]
                area_np = np.array(area, np.int32)

                list_objects = []

                for index, row in px.iterrows():
                    x1, y1, x2, y2 = map(int, row[:4])
                    class_id = int(row[5])
                    class_name = class_list[class_id]

                    if 'car' in class_name:
                        cx = (x1 + x2) // 2
                        cy = (y1 + y2) // 2

                        if cv2.pointPolygonTest(area_np, (cx, cy), False) >= 0:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)
                            list_objects.append(class_name)
                            print(f"Auto erkannt in Parkplatz ID: {parking_id}, Klasse: {class_name}")

                if len(list_objects) > 0:
                    cv2.polylines(frame, [area_np], True, (0, 0, 255), 2)
                    cv2.putText(frame, f"{parking_id}", tuple(area[0]), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1)

                    if not parking["car"]:
                        parking["car"] = True
                        print(f"Parkplatz {parking_id} wurde auf 'belegt' gesetzt.")
                        await update_json()
                else:
                    cv2.polylines(frame, [area_np], True, (0, 255, 0), 2)
                    cv2.putText(frame, f"{parking_id}", tuple(area[0]), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                    if parking["car"]:
                        parking["car"] = False
                        print(f"Parkplatz {parking_id} wurde auf 'frei' gesetzt.")
                        await update_json()

        instructions = [
            "Leertaste: Pause/Weiter",
            "S: Screenshot speichern",
            "Q: Beenden"
        ]

        x_offset = frame.shape[1] - 300
        y_offset = 20
        for i, text in enumerate(instructions):
            cv2.putText(frame, text, (x_offset, y_offset + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        cv2.imshow("RGB", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == 32:
            paused = not paused
        elif key == ord('s'):
            screenshot_filename = f"screenshot_{screenshot_counter}.jpg"
            cv2.imwrite(screenshot_filename, frame)
            print(f"Screenshot gespeichert: {screenshot_filename}")
            screenshot_counter += 1

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    print("IoT Hub Device")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Beendet")
