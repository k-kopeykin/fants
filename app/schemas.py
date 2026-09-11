from pydantic import BaseModel, Field, ConfigDict

class FantasyCreate(BaseModel):
    description: str = Field("Если понравилось, сделай так же ;)", min_length=1, max_length=500)

class FantasyResponse(BaseModel):
    id: int
    description: str
    gif_filename: str
    
    model_config = ConfigDict(from_attributes=True)