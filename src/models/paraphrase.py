from pydantic import BaseModel

class ParaphraseRequest(BaseModel):
    text: str

class ParaphraseResponse(BaseModel):
    paraphrased_text: str 