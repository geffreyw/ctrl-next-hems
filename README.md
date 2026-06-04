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
  - Bron is HomeWizard P1 API (`http://<ip>/api/v1/data`, veld `active_power_w`) indien IP geconfigureerd; fallback is de geconfigureerde HA P1-sensor.

- HEMS Huisverbruik Vermogen
	- Berekend als: `P1 gebruikt + batterij 1 AC vermogen + batterij 2 AC vermogen`.
	- Dit is de waarde die de regel-lus gebruikt vóór modus-specifieke logica (anti-feed / peak-shaving).

- HEMS Batterij 1 Vermogen
- HEMS Batterij 2 Vermogen
	- Deze tonen het aangestuurde batterijvermogen vanuit de controller (niet het gemeten AC-vermogen).
	- Positief betekent ontlaad-commando, negatief betekent laad-commando, nul betekent stop.

- HEMS Plan Summary
  - Samenvatting van het Smart-plan dat om 21:00 ook als melding wordt verstuurd.
  - Attributen bevatten de kwartierverwachting voor SoC, verwacht verbruik, verwachte solar en verwachte import.

- HEMS Plan Doel SoC Ochtendpiek
- HEMS Plan Doel SoC Avondpiek
- HEMS Plan Superdal Laden Nodig
- HEMS Plan Verwachte Minimum SoC
- HEMS Plan Batterijoverschot Vrij
  - Kernwaarden van de Smart-planner voor het dashboard.

- HEMS Gemiddelde Batterij SoC
- HEMS Batterij Totaal Nominaal
- HEMS Batterij Bruikbaar Boven Reserve
  - Batterijcontext voor de planner. Standaard is dit 2 x 5,12 kWh met 15% reserve, dus 8,70 kWh bruikbaar boven reserve.

### Switch

- HEMS Netladen Toestaan
  - Alleen bedoeld voor Manual-modus.
  - Laat de controller extra laadvraag vanaf het net toevoegen zolang de actieve regeling dat toelaat.
  - In `anti_feed` is de importlimiet 0 W, dus deze functie voegt daar geen extra netladen toe.
  - In `peak_shaving` gebruikt de controller vrije ruimte onder de Peak Shaving Limiet om de batterijen bij te laden.

### Select

- HEMS Bedrijfsmodus
  - `off`: HEMS-sturing uit. Batterijen worden naar force mode `stop` gezet en Marstek work mode gaat terug naar `anti_feed`.
  - `manual`: behoudt de bestaande HEMS-regeling op basis van `HEMS Regeling Modus`.
  - `smart`: gebruikt de planner om piekuren op 0 W import te richten, superdal-laden alleen te doen wanneer nodig en import algemeen onder 2200 W te houden.

- HEMS Regeling Modus
	- `anti_feed`: compenseert import/export rond 0 W op basis van het gemeten huisverbruik.
	- `peak_shaving`: ontlaadt alleen boven de ingestelde Peak Shaving Limiet en vermijdt ontladen onder die limiet.

## Configureerbare regelparameters

Na het toevoegen van de integratie maakt Home Assistant meerdere number- en select-entiteiten aan op het CTRL-NEXT HEMS apparaat. Hiermee kun je gedrag tunen zonder code aan te passen.

### Select-entiteit

- HEMS Bedrijfsmodus
  - Hoofdkeuze tussen `off`, `manual` en `smart`.
  - Alleen `smart` voert planner-gestuurde acties uit.

- HEMS Regeling Modus
  - `anti_feed`: compenseert import/export rond 0 W op basis van gemeten huisverbruik.
  - `peak_shaving`: ontlaadt alleen boven de ingestelde Peak Shaving Limiet en vermijdt ontladen bij normaal positief verbruik onder die limiet.

### Number-entiteiten

- HEMS Netlaad Doel SoC (%)
  - Wat dit instelt: Het maximale SoC-doel waar de controller naartoe mag laden zolang `HEMS Netladen Toestaan` actief is.
  - Gedragseffect: Lagere waarden stoppen eerder met laden. Hogere waarden laten langer doorladen richting de ochtend.

- HEMS Max Netlaad Vermogen (W)
  - Wat dit instelt: Het maximale extra laadvermogen dat de controller van het net mag vragen.
  - Gedragseffect: Hogere waarden laden sneller bij vanuit het net. Lagere waarden houden het netladen rustiger. Standaard is dit 500 W.

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

- HEMS Planner Batterijcapaciteit Per Batterij (kWh)
- HEMS Planner Aantal Batterijen
- HEMS Planner Minimale Reserve SoC (%)
- HEMS Planner Veiligheidsmarge (%)
- HEMS Planner Import Limiet (W)
  - Smart-plannerinstellingen. Defaults: 5,12 kWh per batterij, 2 batterijen, 15% reserve, 15% veiligheidsmarge en 2200 W importlimiet.

## Tuning-richtlijnen

- Start conservatief: verhoog eerst stabiliteit en daarna pas responsiviteit.
- Wil je de nieuwe voorspelling gebruiken: kies `smart` bij `HEMS Bedrijfsmodus`.
- Wil je de oude werking behouden: kies `manual` en gebruik `HEMS Regeling Modus` zoals vroeger.
- Wil je 's nachts goedkoop laden in Manual: zet `HEMS Netladen Toestaan` aan via een automation, kies een `HEMS Netlaad Doel SoC (%)`, en beperk het tempo met `HEMS Max Netlaad Vermogen (W)`.
- In `anti_feed` zal netladen geen extra import veroorzaken, omdat de importlimiet daar 0 W blijft.
- In `peak_shaving` laadt de controller alleen bij zolang er nog ruimte is onder de ingestelde Peak Shaving Limiet.
- Zie je frequente modewissels: verhoog Deadband, Deadband Release Margin en/of Minimale Mode Hold Tijd.
- Reageert het systeem te traag: verhoog Filter Alpha of Max Vermogen Stap Per Cyclus.
- Zijn batterij-setpoints te onrustig: verhoog Modbus Cache Drempel.
