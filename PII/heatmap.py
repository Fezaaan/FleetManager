import numpy as np
import matplotlib.pyplot as plt

# Define constants for the heatmap states
BLACK = -1  # No parking ID (not defined field)
WHITE = 0   # Parking ID but no car
RED_1 = 1   # Parking ID, car present, no license plate
GREEN_LP = 2  # Parking ID, car present, with license plate

# Function to check if a point is inside a polygon (Point-in-Polygon Test)
def point_in_polygon(x, y, polygon):
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

# Prepare the heatmap grid
def generate_heatmap(data):
    frame_width = data["global_coordinates"]["ur"][0]
    frame_height = data["global_coordinates"]["ul"][1]

    heatmap = np.full((frame_height, frame_width), BLACK)

    # Iterate over all grid cells and assign values based on parking data
    for park in data["parkings"]:
        polygon = park["coordinates"]
        car = park["car"]
        license_plate = park["license_plate"]
        min_x = min(p[0] for p in polygon)
        max_x = max(p[0] for p in polygon)
        min_y = min(p[1] for p in polygon)
        max_y = max(p[1] for p in polygon)

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if point_in_polygon(x, y, polygon):
                    if car:
                        heatmap[y, x] = GREEN_LP if license_plate else RED_1
                    else:
                        heatmap[y, x] = WHITE

    return heatmap

# Function to handle clicks on the heatmap
def on_click(event, data):
    x, y = int(event.xdata), int(event.ydata)
    for park in data["parkings"]:
        polygon = park["coordinates"]
        if point_in_polygon(x, y, polygon):
            parking_id = park["id"]
            license_plate = park["license_plate"]
            print(f"Clicked on Parking ID: {parking_id}")
            if license_plate:
                print(f"License Plate: {license_plate}")
            else:
                print("No License Plate")
            return
    print("Clicked on an undefined area")

# Plotting the heatmap
def plot_heatmap(data, heatmap):
    fig, ax = plt.subplots(figsize=(10, 10))
    cmap = plt.cm.colors.ListedColormap(['black', 'white', 'red', 'green'])
    bounds = [-1.5, -0.5, 0.5, 1.5, 2.5]
    norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

    ax.imshow(heatmap, cmap=cmap, norm=norm, origin="upper")

    # Overlay parking labels where necessary
    for park in data["parkings"]:
        polygon = np.array(park["coordinates"])
        car = park["car"]
        license_plate = park["license_plate"]
        if car and license_plate:
            # Place the license plate text at the centroid of the parking spot
            centroid_x = np.mean(polygon[:, 0])
            centroid_y = np.mean(polygon[:, 1])
            ax.text(
                centroid_x, centroid_y, license_plate, color="black", fontsize=8, ha="center", va="center"
            )

    fig.canvas.mpl_connect('button_press_event', lambda event: on_click(event, data))
    plt.title("Parking Heatmap with Origin at Top-Left")
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")
    plt.colorbar(ax.imshow(heatmap, cmap=cmap, norm=norm), label="State")
    plt.show()

# Example usage (replace `data` with your JSON data)
data = {
    "global_coordinates": {
        "ul": [0, 500],
        "ur": [1020, 500],
        "ol": [0, 0],
        "or": [1020, 0]
    },
    "parkings": [
        {
            "id": "A",
            "coordinates": [[270, 353], [280, 413], [345, 410], [329, 350]],
            "car": False,
            "license_plate": ""
        },
        {
            "id": "B",
            "coordinates": [[333, 349], [350, 410], [417, 402], [388, 344]],
            "car": False,
            "license_plate": ""
        },
        {
            "id": "C",
            "coordinates": [[394, 344], [423, 400], [483, 392], [447, 339]],
            "car": True,
            "license_plate": ""
        },
        {
            "id": "D",
            "coordinates": [[454, 339], [488, 392], [544, 386], [502, 333]],
            "car": False,
            "license_plate": ""
        },
        {
            "id": "E",
            "coordinates": [[510, 332], [549, 387], [603, 374], [557, 326]],
            "car": True,
            "license_plate": "ABC123"
        },
        {
            "id": "F",
            "coordinates": [[568, 326], [608, 379], [660, 374], [605, 321]],
            "car": True,
            "license_plate": ""
        },
        {
            "id": "G",
            "coordinates": [[611, 319], [665, 371], [710, 363], [653, 317]],
            "car": False,
            "license_plate": ""
        }
    ]
}

heatmap = generate_heatmap(data)
plot_heatmap(data, heatmap)