from pydantic import BaseModel

class QuestionInput(BaseModel):
    question: str