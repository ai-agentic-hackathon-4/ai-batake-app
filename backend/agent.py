import random

def get_weather_from_agent(region: str) -> str:
    """
    Simulates sending a request to an Agent in Agentengine.
    In a real scenario, this might call another service or use an Agent SDK.
    """
    weathers = ["晴れ", "曇り", "雨", "雪", "雷雨"]
    selected_weather = random.choice(weathers)
    return f"{region}の天気は{selected_weather}です。(Agent ID: 001からの報告)"
