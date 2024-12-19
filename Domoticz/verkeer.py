#!/usr/bin/python

import json
import requests
import subprocess

# Instellingen voor het script
NORMAL_DISTANCE = 177.0  # Normale routeafstand in kilometers
DOMOTICZ_IP = "IP"  # Vervang dit door jouw Domoticz IP-adres
DOMOTICZ_IDX = 1360  # IDX van jouw Domoticz device

# Google Maps API: Vul je eigen API-sleutel hieronder in
API_KEY = "API-KEY"  # <-- Vervang dit door je eigen API-sleutel!

# Voer de curl-opdracht uit om de routegegevens op te halen
curl_command = (
    "curl -s 'https://maps.googleapis.com/maps/api/directions/json?"
    "origin=Meezenbroekstraat+31,+Veendam&destination=Emmerik+5,+Westervoort"
    f"&key={API_KEY}&language=nl&departure_time=now' -o route_data.json"
)

# Voer de curl-opdracht uit
subprocess.run(curl_command, shell=True)

# Laad de JSON-gegevens uit het bestand
try:
    with open("route_data.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    print("Fout: route_data.json niet gevonden. Controleer de API-aanroep.")
    exit()

# Controleer of er een route beschikbaar is
if "routes" in data and len(data["routes"]) > 0:
    # Haal de eerste route op
    route = data["routes"][0]
    leg = route["legs"][0]

    # Haal routegegevens op
    distance_text = leg["distance"]["text"]
    distance = float(distance_text.replace(",", ".").split()[0])
    duration_traffic_text = leg["duration_in_traffic"]["value"]
    duration_traffic = int(duration_traffic_text)
    duration_traffic_bericht = leg["duration_in_traffic"]["text"]

    # Controleer of het een afwijkende route is
    if abs(distance - NORMAL_DISTANCE) > 0.05:  # Drempel 50 meter
        route_type = "AFWIJKENDE ROUTE!!"
    else:
        route_type = "Normale route"

    # Verkeersstatus op basis van reistijd
    if duration_traffic < 6600: 
        traffic_status = "rustig verkeer"
    elif 6600 <= duration_traffic < 6840:
        traffic_status = "drukte op de weg"
    elif 6840 <= duration_traffic < 7200:
        traffic_status = "Vertraging!"
    else:
        traffic_status = "Extreme vertraging!!"

    # Bericht opstellen
    message = (
        f"{route_type}, {traffic_status}, {duration_traffic_bericht} "
        f"({distance_text})."
    )

    # Update Domoticz met de route-informatie
    url = (
        f"http://{DOMOTICZ_IP}:8080/json.htm?"
        f"type=command&param=udevice&idx={DOMOTICZ_IDX}&svalue={message}"
    )
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Succesvol bijgewerkt in Domoticz.")
        else:
            print(f"Fout bij het bijwerken van Domoticz: {response.status_code}")
    except Exception as e:
        print(f"Fout bij het bijwerken van Domoticz: {e}")

    # Herlaad het device in Domoticz
    reload_url = f"http://{DOMOTICZ_IP}:8080/json.htm?type=command&param=refreshdevice&idx={DOMOTICZ_IDX}"
    try:
        response = requests.get(reload_url)
        if response.status_code == 200:
            print("Device succesvol herladen in Domoticz.")
        else:
            print(f"Fout bij het herladen van het device in Domoticz: {response.status_code}")
    except Exception as e:
        print(f"Fout bij het herladen van het device in Domoticz: {e}")

else:
    print("Geen routes gevonden in de JSON-gegevens. Controleer je API-aanroep.")
