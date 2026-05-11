# Project Context: CTRL-NEXT HEMS
Dit is een custom Home Assistant integratie voor slim energiemanagement (HEMS) gericht op het aansturen van Marstek batterijen via Modbus.

## Huidige Status: Actieve Modbus-sturing
De integratie stuurt nu daadwerkelijke Home Assistant `switch`/`select`/`number` entiteiten aan om de Marstek batterijen te laden, ontladen of te stoppen. De virtuele sensoren blijven beschikbaar als zicht op het laatst gevraagde batterijvermogen en de berekende virtuele P1-uitkomst.

## Kernlogica (controller.py)
- **Feed-Forward Sturing:** We berekenen het huisverbruik wiskundig: `P1_Netvermogen + Bat1_AC_Power + Bat2_AC_Power`.
- **Load Balancing:** Het benodigde vermogen wordt door 2 gedeeld voor de twee batterijen.
- **Deadband (Dode Band):** Standaard 15W. Kleine schommelingen rond de nul worden genegeerd om pendelen te voorkomen.
- **Modbus Cache Threshold:** Standaard 25W. We sturen pas een nieuw batterijcommando als de gewenste wijziging groter is dan 25W ten opzichte van het vorige commando.
- **Failsafe:** Bij uitschakelen, unload of een fout in de control loop worden beide batterijen naar stop gezet, work mode teruggezet naar Anti-Feed of een equivalente vendor-optie, en Modbus control uitgeschakeld.

## Architectuur / Bestanden
- `config_flow.py`: Vraagt 15 entiteiten op (P1 meter, AC power per batterij, charge/discharge targets, etc.).
- `controller.py`: Bevat de asynchrone loop (draait 1x per seconde) en voert de wiskunde uit. Gebruikt een dispatcher signaal (`ctrl_next_update`).
- `sensor.py`: Virtuele sensoren voor de A/B test (Virtuele P1 meter en Virtuele Batterij output).
- `switch.py`: Hoofdschakelaar om het systeem aan/uit te zetten.
- `number.py`: Sliders om live de deadband en cache threshold aan te passen.
- Alles is gegroepeerd onder één Home Assistant `device` via de `device_info` property in de entiteiten, gekoppeld aan de `entry_id`.