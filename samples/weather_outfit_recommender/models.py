class WeatherSnapshot:
    def __init__(self, temp_c: float, wind_kph: float, condition: str):
        self._temp_c = temp_c
        self._wind_kph = wind_kph
        self._condition = condition

    def get_temp_c(self):
        return self._temp_c

    def set_temp_c(self, temp_c: float):
        self._temp_c = temp_c

    def get_wind_kph(self):
        return self._wind_kph

    def set_wind_kph(self, wind_kph: float):
        self._wind_kph = wind_kph

    def get_condition(self):
        return self._condition

    def set_condition(self, condition: str):
        self._condition = condition


class UnitLookup:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def to_label(self):
        cleaned = self.symbol.strip().lower()
        if cleaned in {"c", "celsius"}:
            return "celsius"
        if cleaned in {"f", "fahrenheit"}:
            return "fahrenheit"
        return cleaned
