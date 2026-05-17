# Home Assistant HEMS Package

Deze map bevat de Home Assistant package met HEMS automations, helpers en scripts.
Beheer je wijzigingen via Git en laat Home Assistant zelf periodiek de laatste versie ophalen via de Git pull add-on.

## 1. Git pull add-on installeren

1. Ga in Home Assistant naar **Instellingen → Add-ons → Add-on winkel**.
2. Zoek op **Git pull** en installeer de add-on.
3. Start de add-on en schakel **Starten bij opstarten** in.

## 2. Git pull add-on configureren

Ga naar het tabblad **Configuratie** van de add-on en stel in:

```yaml
repository: https://github.com/geffreyw/ctrl-next-hems
branch: main
repeat:
  active: true
  interval: 3600
deployment_user: ""
deployment_password: ""
deployment_key: ""
deployment_key_protocol: rsa
```

De add-on kopieert de volledige repo naar `/config` bij elke pull.

## 3. Packages inschakelen in configuration.yaml

Voeg in `/config/configuration.yaml` toe:

```yaml
homeassistant:
  packages: !include_dir_named ha_package/packages
```

Doordat de add-on de repo in `/config` plaatst, ligt het packagebestand daarna op:
`/config/ha_package/packages/hems/hems_automations.yaml`

## 4. Home Assistant herstarten

Herstart Home Assistant na de eerste pull en na het aanpassen van `configuration.yaml`.
Daarna herladen automations en helpers automatisch bij iedere nieuwe pull.

## 5. Integratie-entity IDs

In het package staan standaard de entity_ids uit de CTRL-NEXT HEMS integratie:

- `entity_switch_netladen: switch.hems_netladen_toestaan`
- `entity_number_doel_soc: number.hems_netlaad_doel_soc`
- `entity_number_max_vermogen: number.hems_max_netlaad_vermogen_w`

Pas dit alleen aan als Home Assistant door een naamconflict een suffix toevoegt (bijv. `_2`).