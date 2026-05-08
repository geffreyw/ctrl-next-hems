# Project Context: CTRL-NEXT HEMS
Dit is een custom Home Assistant integratie voor slim energiemanagement (HEMS) gericht op het aansturen van Marstek batterijen via Modbus.

## Huidige Status: "Shadow Mode" / Digital Twin
We draaien momenteel een simulatie. De integratie stuurt geen daadwerkelijke commando's naar de batterijen, maar berekent wat het zou doen en schrijft dit naar virtuele sensoren. Dit gebruiken we als A/B test tegenover het eigen Marstek algoritme (Anti-Feed modus).

## Kernlogica (controller.py)
- **Feed-Forward Sturing:** We berekenen het huisverbruik wiskundig: `P1_Netvermogen + Bat1_AC_Power + Bat2_AC_Power`.
- **Load Balancing:** Het benodigde vermogen wordt door 2 gedeeld voor de twee batterijen.
- **Deadband (Dode Band):** Standaard 15W. Kleine schommelingen rond de nul worden genegeerd om pendelen te voorkomen.
- **Modbus Cache Threshold:** Standaard 25W. We sturen pas een nieuw virtueel commando als de gewenste wijziging groter is dan 25W ten opzichte van het vorige commando.

## Architectuur / Bestanden
- `config_flow.py`: Vraagt 15 entiteiten op (P1 meter, AC power per batterij, charge/discharge targets, etc.).
- `controller.py`: Bevat de asynchrone loop (draait 1x per seconde) en voert de wiskunde uit. Gebruikt een dispatcher signaal (`ctrl_next_update`).
- `sensor.py`: Virtuele sensoren voor de A/B test (Virtuele P1 meter en Virtuele Batterij output).
- `switch.py`: Hoofdschakelaar om het systeem aan/uit te zetten.
- `number.py`: Sliders om live de deadband en cache threshold aan te passen.
- Alles is gegroepeerd onder één Home Assistant `device` via de `device_info` property in de entiteiten, gekoppeld aan de `entry_id`.