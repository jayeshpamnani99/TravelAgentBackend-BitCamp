def generate_trip_plan(destination: str, days: int, interests: list[str]) -> str:
    return f"Here's a {days}-day trip to {destination} focused on {', '.join(interests)}!"
