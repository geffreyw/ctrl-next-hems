# CTRL-NEXT HEMS

Custom Home Assistant integratie om de CTRL-NEXT HEMS batterij-opstelling te sturen via Home Assistant.

Deze repository is een proof of concept en bedoeld voor persoonlijk gebruik.

## HACS installatie

1. Installeer HACS in Home Assistant als dat nog niet gebeurd is.
2. Zorg dat deze repository publiek staat op GitHub.
3. Voeg deze repository in HACS toe als custom repository van type Integratie.
4. Installeer de integratie via HACS.
5. Herstart Home Assistant en voeg de integratie toe via de UI.

## Updates

Deze repository is voorbereid op HACS-updates via GitHub releases. Wanneer je een nieuwe versie wil publiceren:

1. Werk de versie bij in [manifest.json](manifest.json).
2. Maak en push een tag zoals `v0.1.1`.
3. De release-workflow publiceert dan een GitHub release voor die tag.
4. Home Assistant toont daarna de HACS-updateknop voor de nieuwe release.

## Repository-indeling

De integratiebestanden staan in de root van de repository, daarom is HACS geconfigureerd met `content_in_root: true`.

## Entiteiten in Home Assistant

Na installatie maakt de integratie entiteiten aan onder één apparaat (`CTRL-NEXT HEMS Systeem`).

### Sensors

- HEMS P1 Vermogen Gebruikt
	- De exacte P1-waarde die de controller gebruikt om het huisverbruik te berekenen.
	- Bron is HTTP JSON indien geconfigureerd; fallback is de geconfigureerde HA P1-sensor.

- HEMS Huisverbruik Vermogen
	- Berekend als: `P1 gebruikt + batterij 1 AC vermogen + batterij 2 AC vermogen`.
	- Dit is de waarde die de regel-lus gebruikt vóór modus-specifieke logica (anti-feed / peak-shaving).

- HEMS Batterij 1 Vermogen
- HEMS Batterij 2 Vermogen
	- Deze tonen het aangestuurde batterijvermogen vanuit de controller (niet het gemeten AC-vermogen).
	- Positief betekent ontlaad-commando, negatief betekent laad-commando, nul betekent stop.

### Switch

- CTRL-NEXT HEMS Actief
	- Zet de controller-lus aan of uit.

### Select

- HEMS Regeling Modus
	- `anti_feed`: compenseert import/export rond 0 W op basis van het gemeten huisverbruik.
	- `peak_shaving`: ontlaadt alleen boven de ingestelde Peak Shaving Limiet en vermijdt ontladen onder die limiet.

## Configureerbare regelparameters

Na het toevoegen van de integratie maakt Home Assistant meerdere number- en select-entiteiten aan op het CTRL-NEXT HEMS apparaat. Hiermee kun je gedrag tunen zonder code aan te passen.

### Select-entiteit

- HEMS Regeling Modus
  - `anti_feed`: compenseert import/export rond 0 W op basis van gemeten huisverbruik.
  - `peak_shaving`: ontlaadt alleen boven de ingestelde Peak Shaving Limiet en vermijdt ontladen bij normaal positief verbruik onder die limiet.

### Number-entiteiten

- HEMS Peak Shaving Limiet (W)
  - Wat dit instelt: De ontlaaddrempel die alleen in `peak_shaving` modus wordt gebruikt.
  - Gedragseffect: Hogere waarden geven minder ontlaadmomenten (batterij wordt gespaard, meer netpieken toegestaan). Lagere waarden geven meer ontlaadmomenten (vlakker netprofiel, meer batterijgebruik).

- HEMS Deadband (W)
  - Wat dit instelt: Stopdrempel rond 0 W waarbij de controller niet actief laadt/ontlaadt.
  - Gedragseffect: Hogere waarden verminderen schakelen en kleine correcties. Lagere waarden volgen 0 W strakker maar kunnen meer toggling geven.

- HEMS Deadband Release Margin (W)
  - Wat dit instelt: Extra marge boven deadband die nodig is om stop-modus te verlaten.
  - Gedragseffect: Hogere waarden geven sterkere hysterese (stabielere modus, tragere reactie). Lagere waarden reageren sneller maar kunnen meer oscilleren.

- HEMS Filter Alpha
  - Wat dit instelt: Weging van nieuwe metingen in het low-pass filter (0..1).
  - Gedragseffect: Hogere waarden reageren sneller op plotselinge lastwijzigingen. Lagere waarden filteren sterker en verminderen jitter, maar reageren trager.

- HEMS Min Vermogen Per Batterij (W)
  - Wat dit instelt: Minimaal niet-nul doelvermogen per batterij wanneer regeling actief is.
  - Gedragseffect: Hogere waarden vermijden hele kleine, weinig effectieve setpoints maar kunnen grof zijn bij lage lasten. Lagere waarden laten fijnere regeling toe maar kunnen minder nuttige mini-commando's geven.

- HEMS Max Vermogen Stap Per Cyclus (W)
  - Wat dit instelt: Ramp-rate limiter per regelcyclus (1 seconde loop).
  - Gedragseffect: Hogere waarden laten snellere vermogenswijzigingen toe. Lagere waarden geven vloeiendere overgangen en minder abrupte setpoint-sprongen.

- HEMS Minimale Mode Hold Tijd (s)
  - Wat dit instelt: Minimale tijd dat de globale force mode wordt aangehouden voor een nieuwe modewissel is toegestaan.
  - Gedragseffect: Hogere waarden verminderen snelle mode-flips. Lagere waarden laten snellere modewissels toe.

- HEMS Modbus Cache Drempel (W)
  - Wat dit instelt: Minimale setpoint-delta die nodig is voordat een nieuwe Modbus-waarde wordt geschreven.
  - Gedragseffect: Hogere waarden verlagen schrijffrequentie en busbelasting. Lagere waarden updaten vaker en volgen het doelvermogen strakker.

## Tuning-richtlijnen

- Start conservatief: verhoog eerst stabiliteit en daarna pas responsiviteit.
- Zie je frequente modewissels: verhoog Deadband, Deadband Release Margin en/of Minimale Mode Hold Tijd.
- Reageert het systeem te traag: verhoog Filter Alpha of Max Vermogen Stap Per Cyclus.
- Zijn batterij-setpoints te onrustig: verhoog Modbus Cache Drempel.