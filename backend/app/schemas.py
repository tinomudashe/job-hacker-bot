from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class TableColumn(BaseModel):
    key: str
    label: str

class TableData(BaseModel):
    columns: List[TableColumn]
    data: List[Dict[str, Any]]

class FormField(BaseModel):
    type: str  # "text" | "textarea" | "select" | "number" | "email"
    name: str
    label: str
    placeholder: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None  # For select fields
    required: Optional[bool] = False

class FormData(BaseModel):
    fields: List[FormField]
    submitLabel: Optional[str] = "Submit"

class ChartData(BaseModel):
    type: str  # "line" | "bar" | "pie" | etc.
    data: Dict[str, Any]

class PDFData(BaseModel):
    url: str

class MessageContent(BaseModel):
    content: Union[str, TableData, FormData, ChartData, PDFData]
    contentType: str  # "text" | "table" | "form" | "chart" | "pdf"
    appendToPrevious: Optional[bool] = False

class JobSkill(BaseModel):
    name: str
    level: Optional[str] = None
    years: Optional[int] = None

class JobLocation(BaseModel):
    city: str
    state: Optional[str] = None
    country: str
    remote: bool = False

class JobListing(BaseModel):
    id: str
    title: str
    company: str
    location: Union[str, JobLocation]
    salary: Optional[float] = None
    salary_range: Optional[Dict[str, float]] = None
    type: str = Field(..., description="e.g., Full-time, Part-time, Contract")
    skills: Optional[List[Union[str, JobSkill]]] = None
    description: str
    requirements: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    postedDate: datetime
    link: Optional[str] = None

class JobApplication(BaseModel):
    jobId: str
    fullName: str
    email: str
    phone: str
    resume: str  # Base64 encoded file or URL
    coverLetter: Optional[str] = None
    experience: str
    startDate: datetime
    salary: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    references: Optional[str] = None
    additionalInfo: Optional[str] = None

class JobStats(BaseModel):
    chartType: str = Field(..., description="bar, line, or pie")
    data: List[Dict[str, Any]]
    config: Dict[str, str]

class JobMessage(BaseModel):
    type: str = Field(..., description="job_listings, job_stats, job_application, or job_details")
    message: Optional[str] = None
    data: Optional[Union[List[JobListing], JobStats, JobApplication, JobListing]] = None
    config: Optional[Dict[str, Any]] = None 