from langchain_google_genai import ChatGoogleGenerativeAI
import json
import logging
log = logging.getLogger(__name__)

async def _try_browser_extraction(url: str) -> tuple:
        """Try official Playwright Browser tool extraction."""
        try:
            from app.langchain_webbrowser import create_webbrowser_tool
            
            browser_tool = create_webbrowser_tool()
            # Use sync tool in async context
            import asyncio
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, browser_tool.invoke, {"url": url})
            
            if content:
                # Use LLM to extract structured information
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-pro-preview-03-25",
                    temperature=0.1
                )
                
                extraction_prompt = f"""
                Extract job information from this text content. Return ONLY a JSON object with these fields:
                {{
                    "job_title": "job title",
                    "company_name": "company name",
                    "job_description": "job description (concise)",
                    "requirements": "job requirements (concise)"
                }}
                
                Text content:
                {content[:5000]}  # Limit text length
                """
                
                response = await llm.ainvoke(extraction_prompt)
                # Extract JSON from response, handling markdown code blocks
                response_text = response.content
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                job_info = json.loads(response_text)
                
                return True, job_info
            else:
                log.warning(f"Playwright tool returned no content for {url}")
                return False, None
        except Exception as e:
            log.warning(f"Official Playwright extraction failed: {e}")
        return False, None