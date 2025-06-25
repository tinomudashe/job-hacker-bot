import json
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from .schemas import MessageContent, TableData, FormData, ChartData, PDFData, JobMessage, JobListing, JobApplication, JobStats
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_text(self, message: str, websocket: WebSocket, append: bool = False):
        content = MessageContent(
            content=message,
            contentType="text",
            appendToPrevious=append
        )
        await websocket.send_text(content.model_dump_json())

    async def send_table(self, columns: List[Dict[str, str]], data: List[Dict[str, Any]], websocket: WebSocket):
        table_data = TableData(columns=columns, data=data)
        content = MessageContent(
            content=table_data,
            contentType="table"
        )
        await websocket.send_text(content.model_dump_json())

    async def send_form(self, fields: List[Dict[str, Any]], submit_label: str, websocket: WebSocket):
        form_data = FormData(fields=fields, submitLabel=submit_label)
        content = MessageContent(
            content=form_data,
            contentType="form"
        )
        await websocket.send_text(content.model_dump_json())

    async def send_chart(self, chart_type: str, chart_data: Dict[str, Any], websocket: WebSocket):
        chart_data = ChartData(type=chart_type, data=chart_data)
        content = MessageContent(
            content=chart_data,
            contentType="chart"
        )
        await websocket.send_text(content.model_dump_json())

    async def send_pdf(self, pdf_url: str, websocket: WebSocket):
        pdf_data = PDFData(url=pdf_url)
        content = MessageContent(
            content=pdf_data,
            contentType="pdf"
        )
        await websocket.send_text(content.model_dump_json())

    async def send_job_listings(self, websocket: WebSocket, listings: List[JobListing]):
        message = JobMessage(
            type="job_listings",
            message="Here are some job listings that match your criteria:",
            data=listings
        )
        await websocket.send_json(message.dict())

    async def send_job_stats(self, websocket: WebSocket, stats: JobStats):
        message = JobMessage(
            type="job_stats",
            message="Here's an analysis of the job market:",
            data=stats
        )
        await websocket.send_json(message.dict())

    async def send_job_application(self, websocket: WebSocket, job: JobListing):
        message = JobMessage(
            type="job_application",
            message=f"Please fill out the application form for {job.title} at {job.company}",
            data=JobApplication(
                jobId=job.id,
                fullName="",
                email="",
                phone="",
                resume="",
                experience="",
                startDate=datetime.now()
            )
        )
        await websocket.send_json(message.dict())

    async def send_job_details(self, websocket: WebSocket, job: JobListing):
        message = JobMessage(
            type="job_details",
            data=job
        )
        await websocket.send_json(message.dict())

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "search_jobs":
                # Implement job search logic here
                pass
            elif message_type == "apply_job":
                # Handle job application submission
                pass
            elif message_type == "get_job_stats":
                # Generate job market statistics
                pass
            elif message_type == "get_job_details":
                # Fetch detailed job information
                pass
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def process_message(message: str) -> str:
    # Add your message processing logic here
    return f"Received your message: {message}"

async def process_form_submission(data: Dict[str, Any]) -> str:
    # Add your form processing logic here
    return f"Received form data: {json.dumps(data)}" 