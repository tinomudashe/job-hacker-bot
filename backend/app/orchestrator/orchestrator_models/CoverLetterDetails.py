from pydantic import BaseModel, Field

class CoverLetterDetails(BaseModel):
    """The structured data model for a generated cover letter."""
    recipient_name: str = Field(description="Hiring Manager's name, or 'Hiring Team' if unknown.")
    recipient_title: str = Field(description="Hiring Manager's title, or 'Hiring Team' if unknown.")
    company_name: str = Field(description="The name of the company.")
    job_title: str = Field(description="The title of the job being applied for.")
    body: str = Field(description="The full text of the cover letter, in Markdown format.")
    personal_info: dict = Field(description="A dictionary containing the user's personal info.")