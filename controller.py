"""Irrigation decision logic: hysteresis, heat lock and safety timeout."""
DRY_ADC, WET_ADC = 3200, 1300

def moisture_percent(raw, dry=DRY_ADC, wet=WET_ADC):
    """Convert raw ESP32 ADC reading to a clamped 0-100 percentage."""
    if dry == wet:
        raise ValueError("Dry and wet calibration values must differ.")
    value = (dry - raw) * 100.0 / (dry - wet)
    return round(max(0.0, min(100.0, value)), 1)

def decide(moisture, temperature, pump_on, run_seconds=0,
           low=30.0, high=60.0, max_temp=38.0, max_run=120):
    """Return (pump_should_be_on, reason)."""
    if pump_on:
        if moisture >= high:
            return False, "Soil wet enough"
        if run_seconds >= max_run:
            return False, "Safety timeout"
        return True, "Watering in progress"
    if moisture < low:
        if temperature >= max_temp:
            return False, "Too hot - watering postponed"
        return True, "Soil dry"
    return False, "Moisture OK"
