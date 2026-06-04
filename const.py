DOMAIN = "ctrl_next_hems"

# Sensoren algemeen
CONF_P1_SENSOR = "p1_sensor"
CONF_P1_IP_ADDRESS = "p1_ip_address"
DEFAULT_P1_SENSOR = "sensor.p1_meter_power"
DEFAULT_P1_IP_ADDRESS = "192.168.68.55"

# Bedrijfsmodus
CONF_OPERATING_MODE = "operating_mode"
OPERATING_MODE_OFF = "off"
OPERATING_MODE_MANUAL = "manual"
OPERATING_MODE_SMART = "smart"
OPERATING_MODES = [
    OPERATING_MODE_OFF,
    OPERATING_MODE_MANUAL,
    OPERATING_MODE_SMART,
]
DEFAULT_OPERATING_MODE = OPERATING_MODE_MANUAL

# HEMS regeling
CONF_CONTROL_MODE = "control_mode"
CONTROL_MODE_ANTI_FEED = "anti_feed"
CONTROL_MODE_PEAK_SHAVING = "peak_shaving"
CONTROL_MODES = [
    CONTROL_MODE_ANTI_FEED,
    CONTROL_MODE_PEAK_SHAVING,
]

# Instellingen voor de sturing
CONF_DEADBAND = "deadband"
CONF_CACHE_THRESHOLD = "cache_threshold"

# Planner instellingen
CONF_PLANNER_NOTIFY_SERVICE = "planner_notify_service"
CONF_PLANNER_DASHBOARD_PATH = "planner_dashboard_path"
CONF_PLANNER_BATTERY_NOMINAL_KWH_EACH = "planner_battery_nominal_kwh_each"
CONF_PLANNER_BATTERY_COUNT = "planner_battery_count"
CONF_PLANNER_MIN_RESERVE_SOC = "planner_min_reserve_soc"
CONF_PLANNER_SAFETY_MARGIN_PCT = "planner_safety_margin_pct"
CONF_PLANNER_IMPORT_LIMIT_W = "planner_import_limit_w"

DEFAULT_PLANNER_NOTIFY_SERVICE = "notify.mobile_app_iphone_geffrey"
DEFAULT_PLANNER_DASHBOARD_PATH = "/dashboard-hems-solar/planning"
DEFAULT_PLANNER_BATTERY_NOMINAL_KWH_EACH = 5.12
DEFAULT_PLANNER_BATTERY_COUNT = 2
DEFAULT_PLANNER_MIN_RESERVE_SOC = 15.0
DEFAULT_PLANNER_SAFETY_MARGIN_PCT = 15.0
DEFAULT_PLANNER_IMPORT_LIMIT_W = 2200.0

# Forecast.Solar
CONF_FORECAST_SOLAR_TODAY = "forecast_solar_today"
CONF_FORECAST_SOLAR_REMAINING_TODAY = "forecast_solar_remaining_today"
CONF_FORECAST_SOLAR_TOMORROW = "forecast_solar_tomorrow"
CONF_FORECAST_SOLAR_THIS_HOUR = "forecast_solar_this_hour"
CONF_FORECAST_SOLAR_NEXT_HOUR = "forecast_solar_next_hour"
CONF_FORECAST_SOLAR_POWER_NOW = "forecast_solar_power_now"
CONF_FORECAST_SOLAR_POWER_IN_24H = "forecast_solar_power_in_24h"
CONF_FORECAST_SOLAR_PEAK_TODAY = "forecast_solar_peak_today"
CONF_FORECAST_SOLAR_PEAK_TOMORROW = "forecast_solar_peak_tomorrow"

DEFAULT_FORECAST_SOLAR_TODAY = "sensor.solar_production_forecast_estimated_energy_production_today"
DEFAULT_FORECAST_SOLAR_REMAINING_TODAY = "sensor.solar_production_forecast_estimated_energy_production_remaining_today"
DEFAULT_FORECAST_SOLAR_TOMORROW = "sensor.solar_production_forecast_estimated_energy_production_tomorrow"
DEFAULT_FORECAST_SOLAR_THIS_HOUR = "sensor.solar_production_forecast_estimated_energy_production_this_hour"
DEFAULT_FORECAST_SOLAR_NEXT_HOUR = "sensor.solar_production_forecast_estimated_energy_production_next_hour"
DEFAULT_FORECAST_SOLAR_POWER_NOW = "sensor.solar_production_forecast_estimated_power_production_now"
DEFAULT_FORECAST_SOLAR_POWER_IN_24H = "sensor.solar_production_forecast_estimated_power_production_in_24_hours"
DEFAULT_FORECAST_SOLAR_PEAK_TODAY = "sensor.solar_production_forecast_highest_power_peak_time_today"
DEFAULT_FORECAST_SOLAR_PEAK_TOMORROW = "sensor.solar_production_forecast_highest_power_peak_time_tomorrow"

# Batterij 1
CONF_BATTERY_1_SOC = "battery_1_soc"
CONF_BAT1_CHARGE = "bat1_charge_power"
CONF_BAT1_DISCHARGE = "bat1_discharge_power"
CONF_BAT1_FORCE_MODE = "bat1_force_mode"
CONF_BAT1_MODBUS_SWITCH = "bat1_modbus_switch"
CONF_BAT1_WORK_MODE = "bat1_work_mode"
CONF_BAT1_AC_POWER = "bat1_ac_power"
DEFAULT_BATTERY_1_SOC = "sensor.marstek_ve3_1_battery_soc"
DEFAULT_BAT1_CHARGE = "number.marstek_ve3_1_set_charge_power"
DEFAULT_BAT1_DISCHARGE = "number.marstek_ve3_1_set_discharge_power"
DEFAULT_BAT1_FORCE_MODE = "select.marstek_ve3_1_force_mode"
DEFAULT_BAT1_MODBUS_SWITCH = "switch.marstek_ve3_1_rs485_control_mode"
DEFAULT_BAT1_WORK_MODE = "select.marstek_ve3_1_user_work_mode"
DEFAULT_BAT1_AC_POWER = "sensor.marstek_ve3_1_ac_power"

# Batterij 2
CONF_BATTERY_2_SOC = "battery_2_soc"
CONF_BAT2_CHARGE = "bat2_charge_power"
CONF_BAT2_DISCHARGE = "bat2_discharge_power"
CONF_BAT2_FORCE_MODE = "bat2_force_mode"
CONF_BAT2_MODBUS_SWITCH = "bat2_modbus_switch"
CONF_BAT2_WORK_MODE = "bat2_work_mode"
CONF_BAT2_AC_POWER = "bat2_ac_power"
DEFAULT_BATTERY_2_SOC = "sensor.marstek_ve3_2_battery_soc"
DEFAULT_BAT2_CHARGE = "number.marstek_ve3_2_set_charge_power"
DEFAULT_BAT2_DISCHARGE = "number.marstek_ve3_2_set_discharge_power"
DEFAULT_BAT2_FORCE_MODE = "select.marstek_ve3_2_force_mode"
DEFAULT_BAT2_MODBUS_SWITCH = "switch.marstek_ve3_2_rs485_control_mode"
DEFAULT_BAT2_WORK_MODE = "select.marstek_ve3_2_user_work_mode"
DEFAULT_BAT2_AC_POWER = "sensor.marstek_ve3_2_ac_power"
