# Project Requirements & Roadmap: CTRL-NEXT HEMS

## Doelstelling
Het creëren van een intelligent Home Energy Management System (HEMS) dat de Marstek/Venus batterijen (2 units) aanstuurt om de energiekosten te minimaliseren, rekening houdend met het Belgische net-context (capaciteitstarief en Engie contracten).

## Hardware & Omgeving
- **Batterijen:** 2x Marstek (Venus) omvormers/batterij-systemen.
- **Communicatie:** Modbus RS485 (via Home Assistant switches/numbers/selects).
- **Meting:** P1-meter (real-time import/export data).
- **Locatie:** België (relevante factoren: capaciteitstarief en specifieke Engie tariefstructuren).

## Specifieke Requirements

### 1. Zero-Export (Huidige focus)
- Het systeem moet de P1-meter zo dicht mogelijk op 0W houden.
- Gebruik van Feed-Forward sturing door actueel huisverbruik te berekenen.
- Load balancing: Het benodigde vermogen gelijkmatig verdelen over beide batterijen.

### 2. Peak Shaving (Capaciteitstarief)
- **Doel:** De maandpiek (gemiddeld kwartiervermogen) onder een bepaalde grens houden (bijv. 2.5 kW).
- **Logica:** Zodra de P1-meter een afname detecteert die de limiet nadert, moeten de batterijen met prioriteit ontladen, ongeacht de andere instellingen.

### 3. Engie Super-dal Optimalisatie
- **Tarief:** Gebruik maken van de Engie Super-dal uren (zeer goedkoop laden 's nachts).
- **Beslisboom:** - Laden van het net tijdens super-dal uren.
    - De hoeveelheid bij te laden energie moet afhankelijk zijn van de zonnevoorspelling van de volgende dag.

### 4. Forecast.Solar Integratie
- Het systeem moet de `forecast.solar` integratie in Home Assistant uitlezen.
- **Scenario:** Als er morgen veel zon wordt voorspeld, moet de batterij 's nachts niet (vol)geladen worden vanuit het net, om ruimte te houden voor gratis zonne-energie.
- **Scenario:** Als er morgen weinig zon is, moet de batterij tijdens super-dal maximaal laden om de dure daguren te overbruggen.

### 5. Veiligheid & Failsafe
- Bij het stoppen van de integratie of een crash van de controller, moeten de batterijen onmiddellijk terugkeren naar de "Anti-Feed" (User Work Mode) en Modbus control moet worden uitgeschakeld.
- Dit voorkomt dat batterijen blijven hangen in een geforceerde laad/ontlaad staat.

## Toekomstige Uitbreidingen
- Dynamische prijzen integratie (indien overgestapt wordt van Engie vast/variabel naar dynamisch).
- Prioriteitsbeheer voor EV-laden in combinatie met batterij-ontlading.