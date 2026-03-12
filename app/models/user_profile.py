from pydantic import BaseModel


class UserProfile(BaseModel):
    user_id: str
    age: int
    gender: str
    location: str
    religion: str
    diet_type: str
    health_conditions: list


class DailyActivity(BaseModel):
    steps: int
    calories: int
    heart_rate: int
    sleep_hours: float
