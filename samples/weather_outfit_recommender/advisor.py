class WeatherProfile:
    def __init__(self, temp: float, wind: float, condition: str):
        self.temp = temp
        self.wind = wind
        self.condition = condition
        self.is_precip = condition in {"rain", "snow"}


class OutfitAdvisor:
    def recommend(self, profile: WeatherProfile):
        score = profile.temp - (profile.wind * 0.1)
        if profile.is_precip:
            score -= 3
        if profile.condition == "hail":
            score -= 6
        if profile.temp < 0:
            return ["parka", "boots", "gloves"]
        if score < 5:
            return ["coat", "scarf"]
        return ["jacket"]
