# Entity Inventory

## Solar (Solis Inverter)

### PV Production
- `sensor.solis_s6_eh3p_total_pv_power` — Total PV power (W)
- `sensor.solis_s6_eh3p_pv_power_1` — PV1 (South) power
- `sensor.solis_s6_eh3p_pv_power_2` — PV2 (West) power
- `sensor.solis_s6_eh3p_pv_today_energy_generation` — Today's PV generation
- `sensor.solis_s6_eh3p_pv_total_energy_generation` — Total lifetime generation

### Battery (Dyness)
- `sensor.solis_s6_eh3p_battery_soc` — State of charge (%)
- `sensor.solis_s6_eh3p_battery_power` — Charge/discharge power (W)
- `sensor.solis_s6_eh3p_battery_voltage` — Voltage (V)
- `sensor.solis_s6_eh3p_battery_current` — Current (A)
- `sensor.solis_s6_eh3p_today_battery_charge_energy` — Today's charge (kWh)
- `sensor.solis_s6_eh3p_today_battery_discharge_energy` — Today's discharge (kWh)
- `sensor.solis_s6_eh3p_lead_acid_battery_temperature` — Battery temperature
- `sensor.battery_energy_kwh` — Current stored energy (kWh)
- `sensor.battery_energy_available` — Available energy (kWh)
- `sensor.battery_energy_needed` — Energy needed to full (kWh)
- `sensor.dyness_adaptive_reserve` — Adaptive reserve (kWh)

### Grid
- `sensor.solis_s6_eh3p_meter_total_active_power` — Grid power (W)
- `sensor.solis_s6_eh3p_today_energy_imported_from_grid` — Today's import (kWh)
- `sensor.solis_s6_eh3p_today_energy_fed_into_grid` — Today's export (kWh)
- `sensor.solis_s6_eh3p_today_energy_consumption` — Today's consumption (kWh)
- `sensor.solis_s6_eh3p_household_load_power` — Household load (W)
- `sensor.solis_s6_eh3p_grid_frequency` — Grid frequency (Hz)

### Inverter
- `sensor.solis_s6_eh3p_active_power` — Inverter output power
- `sensor.solis_s6_eh3p_current_status` — Operating status
- `sensor.solis_s6_eh3p_temperature` — Inverter temperature
- `sensor.solis_s6_eh3p_a_phase_voltage` — Phase A voltage
- `sensor.solis_s6_eh3p_a_phase_current` — Phase A current

## EV (IONIQ 5)

### Vehicle Status (Kia UVO)
- `sensor.ioniq_5_ev_battery_level` — Battery level (%)
- `sensor.ioniq_5_ev_range` — Estimated range (km)
- `sensor.ioniq_5_total_driving_range` — Total driving range
- `sensor.ioniq_5_odometer` — Odometer (km)
- `sensor.ioniq_5_ev_charging_power` — Charging power (W)
- `sensor.ioniq_5_estimated_charge_duration` — Time to full (min)
- `sensor.ioniq_5_last_updated_at` — Last vehicle update
- `sensor.ioniq_5_average_energy_consumption` — Avg consumption (Wh/km)
- `binary_sensor.ioniq_5_ev_battery_charge` — Is charging
- `binary_sensor.ioniq_5_ev_battery_plug` — Is plugged in
- `binary_sensor.ioniq_5_locked` — Door lock status
- `device_tracker.ioniq_5_location` — Vehicle location
- `lock.ioniq_5_door_lock` — Door lock control
- `climate.ioniq_5_climate_control` — Cabin climate

### Charging Station (Wallbox 22k07)
- `sensor.22k07_charging_station_charging_power` — Charge power (W)
- `sensor.22k07_charging_station_work_state` — Work state
- `sensor.22k07_charging_station_total_energy` — Total energy (kWh)
- `switch.22k07_charging_station_start_stop` — Start/stop charging
- `number.22k07_charging_station_charge_current` — Charge current (A)

### EV Smart Charging
- `input_select.ev_charge_mode` — Charge mode (auto/top_up_50/trip_100)
- `input_number.ev_target_soc` — Target SOC (%)
- `sensor.ev_target_soc_effective` — Effective target SOC
- `sensor.ev_usable_surplus` — Available surplus (kWh)
- `sensor.ev_power_kw` — EV power (kW)
- `sensor.ev_energy_available` — Available energy for EV
- `sensor.ev_charging_amps_suggested` — Suggested charge current
- `sensor.ev_priority_index` — Priority index
- `input_boolean.ev_force_charge_today` — Force charge today
- `input_boolean.ev_stop_requested` — Stop requested

## Pool

### Pump & Temperature
- `switch.medence_szivattyu_biztositek` — Pump switch
- `sensor.medence_cso_homero_probe_temperature` — Water temperature (°C)
- `input_number.medence_utolso_homerseklet` — Cached temperature
- `sensor.medence_szivattyu_biztositek_power` — Pump power (W)
- `sensor.medence_cso_homero_battery` — Probe battery (%)
- `sensor.medence_meres_allapota` — Measurement status

### Control
- `input_number.pool_pump_daily_total_runtime` — Daily runtime (h)
- `input_datetime.pool_pump_stop_time` — Pump stop time
- `input_button.pool_pump_extend_time` — Extend runtime (+1h)
- `input_button.pool_pump_reduce_time` — Reduce runtime (-1h)
- `switch.medence_vilagitas_biztositek` — Pool light

### Power
- `sensor.2_es_medence_biztositek_power` — Pool circuit power
- `sensor.medence_szivattyu_biztositek_power` — Pump power

## Climate

### HVAC
- `climate.nappali_klima` — Living room AC
- `climate.master_bedroom` — Bedroom AC
- `climate.nappali_padlofutes` — Living room underfloor heating
- `climate.szoba_padlo_futes` — Bedroom underfloor heating

## Temperature & Humidity

### Sensors
- `sensor.nappali_homero_temperature` / `sensor.nappali_homero_humidity` — Living room
- `sensor.halo_homero_temperature` / `sensor.halo_homero_humidity` — Bedroom
- `sensor.gyerek_szoba_homero_temperature` / `sensor.gyerek_szoba_homero_humidity` — Kids room
- `sensor.furdo_homero_temperature` / `sensor.furdo_homero_humidity` — Bathroom
- `sensor.pince_homero_temperature` / `sensor.pince_homero_humidity` — Basement
- `sensor.terasz_homero_temperature` / `sensor.terasz_homero_humidity` — Terrace
- `sensor.garazs_homero_temperature` — Garage

## Lights

- `light.konyha_csap_vilagitas` — Kitchen tap light
- `light.wled` — WLED strip
- `light.athidalo` — Bridge light (with party mode)
- `switch.pince_terasz_hangulat_vilagitas` — Basement terrace ambient light
- `light.11kw_charger_auto_tolto` — EV charger light

## Basement

### Devices
- `button.wake_on_lan_b4_2e_99_d1_c0_37` — Desktop WoL
- `button.desktop_nia5fgv_hibernate` — Desktop hibernate
- `binary_sensor.pince_mozgas_erzekelo_presence` — Motion sensor
- `sensor.iroda_aram_mero_power` — Office power meter
- `sensor.nem_mert_fogyasztasok` — Unmeasured loads

### Power Monitoring
- `sensor.bojler_aram_mero_power` — Boiler
- `sensor.pince_huto_power` — Fridge
- `sensor.pince_melyhuto_power` — Freezer
- `sensor.klima_aram_mero_power` — AC
- `sensor.konyha_huto_power` — Kitchen fridge
- `sensor.mosogep_power` — Washing machine
- `sensor.szaritogep_power` — Dryer
- `sensor.pince_nagy_huto_power` — Large fridge

## Homelab

### TrueNAS
- `update.truenas_update` — Available updates

### Zigbee2MQTT
- `binary_sensor.zigbee2mqtt_bridge_connection_state` — Bridge state
- `sensor.zigbee2mqtt_bridge_version` — Version
- `button.zigbee2mqtt_bridge_restart` — Restart bridge
- `select.zigbee2mqtt_bridge_log_level` — Log level
- `switch.zigbee2mqtt_bridge_permit_join` — Permit join

### Home Assistant
- `sensor.backup_backup_manager_state` — Backup state
- `sensor.backup_next_scheduled_automatic_backup` — Next backup

## Weather & Forecast

- `weather.forecast_home` — Weather forecast
- `sensor.pv_forecast_total` — Total PV forecast (kWh)
- `sensor.energy_production_today_2` — West PV today
- `sensor.energy_production_today_3` — South PV today
- `sensor.power_production_now_2` — West PV now (W)
- `sensor.power_production_now_3` — South PV now (W)
- `sensor.sun_next_dusk` — Sunset time

## Energy Costs

- `sensor.import_rezsi_kwh` — Reszsi import (kWh)
- `sensor.import_piaci_kwh` — Piaci import (kWh)
- `sensor.import_osszes_koltseg` — Total cost (HUF)
- `sensor.solis_s6_eh3p_today_energy_imported_from_grid_cost` — Import cost
- `sensor.solis_s6_eh3p_today_energy_fed_into_grid_compensation` — Export compensation
