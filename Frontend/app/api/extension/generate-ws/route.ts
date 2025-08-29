import { NextRequest, NextResponse } from "next/server";

// Dynamic import to avoid build-time issues
let WebSocket: any;
try {
  WebSocket = require('ws');
} catch (e) {
  console.warn('ws module not available, using global WebSocket');
  WebSocket = global.WebSocket;
}

interface ExtensionJobData {
  title?: string;
  company?: string;
  location?: string;
  description?: string;
  url?: string;
  type?: string;
  salary?: string;
}

interface GenerateRequest {
  jobData: ExtensionJobData;
  documentType: 'resume' | 'cover_letter';
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL = API_URL.replace(/^http/, "ws");

export async function POST(request: NextRequest) {
  try {
    // Get authorization header
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader) {
      return NextResponse.json(
        { error: "No authorization header" },
        { status: 401 }
      );
    }

    // Extract token from Bearer header
    const token = authHeader.replace('Bearer ', '');
    
    // Log token type for debugging
    console.log('Token received:', {
      isExtensionToken: token.startsWith('jhb_'),
      tokenPrefix: token.substring(0, 10),
      authHeader: authHeader.substring(0, 20) + '...'
    });
    
    // Parse request body
    const body: GenerateRequest = await request.json();
    const { jobData, documentType } = body;

    if (!jobData || !documentType) {
      return NextResponse.json(
        { error: "Missing required fields: jobData and documentType" },
        { status: 400 }
      );
    }

    // Create a promise to handle WebSocket communication
    const result = await new Promise<string>((resolve, reject) => {
      // Create WebSocket connection with token (Note: orchestrator router has /api prefix)
      const wsUrl = `${WS_URL}/api/ws/orchestrator?token=${encodeURIComponent(token)}&page_id=extension_temp_${Date.now()}`;
      console.log('Connecting to WebSocket:', wsUrl.replace(token, 'TOKEN_HIDDEN'));
      
      const ws = new WebSocket(wsUrl);
      
      let responseContent = '';
      let timeoutId: NodeJS.Timeout;
      let messagesSent = 0;
      
      // Set a timeout - increased to 3 minutes for resume generation
      timeoutId = setTimeout(() => {
        ws.close();
        reject(new Error('WebSocket timeout - no response received'));
      }, 180000); // 3 minutes timeout
      
      // Function to send the initial message
      const sendInitialMessage = () => {
        console.log('WebSocket connected for extension generation');
        
        // Craft the message based on document type
        let content = '';
        
        if (documentType === 'cover_letter') {
          content = `Please generate a professional cover letter for the following job:

Job Title: ${jobData.title || 'Not specified'}
Company: ${jobData.company || 'Not specified'}
Location: ${jobData.location || 'Not specified'}
${jobData.type ? `Job Type: ${jobData.type}` : ''}
${jobData.salary ? `Salary: ${jobData.salary}` : ''}

Job Description:
${jobData.description || 'No description provided'}

Please create a compelling cover letter that highlights relevant skills and experience for this position.`;
        } else {
          content = `Act as a professional resume writer. Your task is to optimize my existing resume for ATS systems and the job below, while maintaining 100% accuracy and authenticity.

STRICT ETHICAL GUIDELINES:
• Work ONLY with information already present in my resume
• Do NOT fabricate, invent, or exaggerate any experience, skills, or achievements
• Do NOT add company names, projects, or certifications that don't exist in my current resume
• Maintain factual accuracy - if something cannot be verified from my existing resume, do not include it

TAILORING APPROACH:
1. ANALYZE the job description to identify key skills, keywords, and requirements
2. REORGANIZE my existing content to prioritize the most relevant experience
3. REPHRASE bullet points using action verbs and keywords from the job description (while keeping facts unchanged)
4. OPTIMIZE the professional summary to highlight relevant existing skills
5. ENSURE ATS compatibility by using standard section headers and relevant keywords

PROFESSIONAL SUMMARY RULES:
• Keep it generic and professional - no company names or "for this role" language
• Focus on my proven skills and experience
• Use format: "[Years of experience] [Role/Industry] professional with expertise in [relevant skills from my resume]"
• GOOD Examples: 
  - "Experienced marketing professional with 7+ years developing data-driven campaigns and managing cross-functional teams"
  - "Senior software engineer with expertise in distributed systems, microservices architecture, and DevOps practices"
  - "Results-oriented project manager with proven track record of delivering complex technical projects on time and within budget"
• BAD Examples:
  - "Eager to leverage my skills for Nityo Infotech's pharmaceutical clients"
  - "Looking to contribute to your company's email marketing initiatives"
  - "Seeking to apply my expertise to drive innovative solutions at your organization"
• Do NOT write: "Eager to join...", "Looking to contribute to...", or mention any company
• Do NOT use phrases like "eager to leverage", "seeking to", "looking to apply"
• Do NOT reference the specific job, company, or industry you're applying to
• Write in third person or neutral tone: "Experienced professional with..." not "Eager to..."
• The summary should be universally applicable to any similar role
• Focus on what you HAVE DONE and CAN DO, not what you WANT TO DO

BULLET POINT OPTIMIZATION:
• Start with strong action verbs (managed, developed, implemented, achieved)
• Include metrics and quantifiable results that already exist in my resume
• Match terminology from the job description where my experience aligns
• Keep each bullet concise (1-2 lines maximum)

Job Title: ${jobData.title || 'Not specified'}
Job Description:
${jobData.description || 'No description provided'}

OUTPUT REQUIREMENTS:
1. Return my tailored resume maintaining all original factual information
2. Highlight in your changes which keywords from the job description you've matched
3. Ensure the resume remains truthful and can be verified in an interview
4. Keep length appropriate (1-2 pages for most roles)

Remember: This is a professional CV/resume document, not a cover letter. I must be able to honestly discuss everything on this resume in an interview.`;
        }
        
        // Send the message with correct format for orchestrator
        const messageToSend = {
          type: 'message',
          content: content,  // orchestrator expects 'content' field for message text
          page_id: `extension_temp_${Date.now()}`,
          timestamp: new Date().toISOString()
        };
        
        console.log('Sending message to WebSocket:', messageToSend);
        messagesSent++;
        ws.send(JSON.stringify(messageToSend));
        console.log(`Message ${messagesSent} sent successfully`);
      };
      
      // Check if WebSocket is already open, otherwise wait for open event
      console.log('WebSocket readyState:', ws.readyState);
      if (ws.readyState === 1) { // 1 = OPEN
        sendInitialMessage();
      } else {
        ws.on('open', () => {
          console.log('WebSocket open event fired');
          sendInitialMessage();
        });
      }
      
      ws.on('message', (data: any) => {
        console.log('Received WebSocket message:', data.toString().substring(0, 200));
        try {
          const parsed = JSON.parse(data.toString());
          console.log('Parsed message type:', parsed.type);
          
          // Handle different message types
          switch (parsed.type) {
            case 'message':
              // This is the AI response
              if (parsed.message && !parsed.isUser) {
                responseContent += parsed.message;  // Accumulate content
                console.log('Received message chunk, total length:', responseContent.length);
              }
              break;
              
            case 'complete':
              // Message generation complete
              console.log('Generation complete, final content length:', responseContent.length);
              clearTimeout(timeoutId);
              ws.close();
              if (responseContent) {
                resolve(responseContent);
              } else {
                reject(new Error('No content received from AI'));
              }
              break;
              
            case 'error':
              clearTimeout(timeoutId);
              ws.close();
              
              // Check for subscription errors
              if (parsed.message?.includes('subscription') || parsed.message?.includes('limit')) {
                reject(new Error('Subscription required: ' + parsed.message));
              } else {
                reject(new Error(parsed.message || 'Generation failed'));
              }
              break;
              
            case 'subscription_required':
              clearTimeout(timeoutId);
              ws.close();
              reject(new Error('Active subscription required to use this feature'));
              break;
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      });
      
      ws.on('error', (error: any) => {
        clearTimeout(timeoutId);
        console.error('WebSocket error:', error);
        reject(new Error('WebSocket connection failed'));
      });
      
      ws.on('close', (code: any, reason: any) => {
        console.log(`WebSocket closed with code ${code}, reason: ${reason}`);
        clearTimeout(timeoutId);
        if (!responseContent) {
          reject(new Error(`Connection closed without response (code: ${code})`));
        }
      });
    });

    // Parse the cover letter content if it contains the DOWNLOADABLE_COVER_LETTER marker
    let processedContent = result;
    let coverLetterId = null;
    let parsedData = null;
    
    if (documentType === 'cover_letter' && result.includes('[DOWNLOADABLE_COVER_LETTER]')) {
      try {
        // Extract JSON from the marker
        const jsonStart = result.indexOf('{');
        const jsonEnd = result.lastIndexOf('}') + 1;
        if (jsonStart !== -1 && jsonEnd > jsonStart) {
          const jsonContent = result.substring(jsonStart, jsonEnd);
          parsedData = JSON.parse(jsonContent);
          
          // Extract the cover letter ID if present
          if (parsedData.id) {
            coverLetterId = parsedData.id;
          }
          
          // Format the cover letter properly
          processedContent = `Dear ${parsedData.recipient_name || 'Hiring Team'},\n\n${parsedData.body}`;
        }
      } catch (parseError) {
        console.error('Error parsing cover letter JSON:', parseError);
        // Keep original content if parsing fails
      }
    }

    // Format the response based on document type
    if (documentType === 'cover_letter') {
      return NextResponse.json({
        success: true,
        documentType: 'cover_letter',
        content: processedContent,
        coverLetterId: coverLetterId,
        fullData: parsedData, // Include full parsed data
        companyName: jobData.company || parsedData?.company_name,
        jobTitle: jobData.title || parsedData?.job_title,
        jobUrl: jobData.url
      });
    } else {
      return NextResponse.json({
        success: true,
        documentType: 'resume',
        content: result,
        tailoringPrompt: result,
        companyName: jobData.company,
        jobTitle: jobData.title,
        jobUrl: jobData.url
      });
    }

  } catch (error) {
    console.error("Error in WebSocket generation:", error);
    
    const errorMessage = error instanceof Error ? error.message : 'Generation failed';
    
    // Check if it's a subscription error
    if (errorMessage.includes('subscription') || errorMessage.includes('Subscription')) {
      return NextResponse.json(
        { 
          error: "Subscription required",
          details: "You need an active subscription (trial or pro) to use this feature"
        },
        { status: 402 } // Payment Required
      );
    }
    
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    );
  }
}

// CORS headers for extension access
export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}