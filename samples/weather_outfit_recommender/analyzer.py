class ForecastAnalyzer:
    def score(self, temp: float, wind: float, humidity: float, precip: float, uv: float, cloud: float):
        score = 0
        if temp < 0 and wind > 15 and humidity > 70:
            score -= 2
        if temp < 5 and wind > 10 and precip > 0.2:
            score -= 2
        if temp < 10 and humidity > 80 and cloud > 0.6:
            score -= 1
        if temp > 30 and uv > 7 and humidity > 50:
            score += 2
        if temp > 25 and wind < 5 and cloud < 0.2:
            score += 1
        if temp > 20 and precip == 0 and uv > 6:
            score += 1
        return score
