import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";

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

export async function POST(request: NextRequest) {
  try {
    // Get authorization header
    const authHeader = request.headers.get('Authorization');
    let token: string | null = null;
    let isExtensionToken = false;

    if (authHeader) {
      // Check if it's an extension token
      if (authHeader.startsWith('Bearer jhb_')) {
        // This is an extension token, verify it
        token = authHeader.replace('Bearer ', '');
        isExtensionToken = true;
        
        // Verify the extension token
        const verifyResponse = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'}/api/extension-tokens/verify`,
          {
            method: 'POST',
            headers: {
              'Authorization': authHeader,
            },
          }
        );

        if (!verifyResponse.ok) {
          return NextResponse.json(
            { error: "Invalid or expired extension token" },
            { status: 401 }
          );
        }
      } else {
        // Regular session token
        token = authHeader.replace('Bearer ', '');
      }
    } else {
      // Try to get session token
      const session = await auth();
      token = await session?.getToken();
    }

    if (!token) {
      return NextResponse.json(
        { error: "Unauthorized - Please sign in or use an extension token" },
        { status: 401 }
      );
    }

    // Parse request body
    const body: GenerateRequest = await request.json();
    const { jobData, documentType } = body;

    if (!jobData || !documentType) {
      return NextResponse.json(
        { error: "Missing required fields: jobData and documentType" },
        { status: 400 }
      );
    }

    // Get user's resume data first
    const backendAuth = authHeader || `Bearer ${token}`;
    const resumeResponse = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'}/api/resume`,
      {
        headers: {
          Authorization: backendAuth,
        },
      }
    );

    if (!resumeResponse.ok) {
      return NextResponse.json(
        { error: "Failed to fetch user resume data" },
        { status: 500 }
      );
    }

    const resumeData = await resumeResponse.json();

    if (documentType === 'cover_letter') {
      // Generate cover letter
      const coverLetterPayload = {
        job_description: jobData.description || '',
        company_name: jobData.company || '',
        job_title: jobData.title || '',
        user_profile: {
          name: resumeData.personalInfo?.name || '',
          email: resumeData.personalInfo?.email || '',
          phone: resumeData.personalInfo?.phone || '',
          address: resumeData.personalInfo?.location || '',
          linkedin: resumeData.personalInfo?.linkedin || '',
          summary: resumeData.personalInfo?.summary || ''
        },
        user_skills: resumeData.skills?.join(', ') || ''
      };

      // Use the original auth header for backend calls
      const backendAuthHeader = isExtensionToken ? authHeader! : `Bearer ${token}`;
      
      const coverLetterResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'}/api/cover-letters/generate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': backendAuthHeader,
          },
          body: JSON.stringify(coverLetterPayload),
        }
      );

      if (!coverLetterResponse.ok) {
        const errorData = await coverLetterResponse.text();
        console.error('Cover letter generation failed:', {
          status: coverLetterResponse.status,
          statusText: coverLetterResponse.statusText,
          error: errorData,
          authUsed: isExtensionToken ? 'extension token' : 'session token',
        });
        return NextResponse.json(
          { 
            error: "Failed to generate cover letter",
            details: coverLetterResponse.status === 403 ? 
              "Authentication failed. The backend may not support extension tokens for this endpoint yet." : 
              errorData 
          },
          { status: coverLetterResponse.status }
        );
      }

      const coverLetterData = await coverLetterResponse.json();
      
      // Format the cover letter content
      const formattedContent = formatCoverLetter(coverLetterData.structured_cover_letter);

      return NextResponse.json({
        success: true,
        documentType: 'cover_letter',
        content: formattedContent,
        companyName: jobData.company,
        jobTitle: jobData.title,
        jobUrl: jobData.url
      });

    } else if (documentType === 'resume') {
      // For resume tailoring, we'll send a message to generate tailored content
      // This is a simplified version - you might want to implement a more sophisticated tailoring
      
      const tailoringPrompt = `Please help me tailor my resume for this position:
      
Job Title: ${jobData.title}
Company: ${jobData.company}
Location: ${jobData.location || 'Not specified'}
${jobData.type ? `Job Type: ${jobData.type}` : ''}
${jobData.salary ? `Salary: ${jobData.salary}` : ''}

Job Description:
${jobData.description || 'No description provided'}

Please analyze this job posting and suggest how to tailor my resume to better match the requirements.`;

      // Return the existing resume with tailoring suggestions
      return NextResponse.json({
        success: true,
        documentType: 'resume',
        content: resumeData,
        tailoringPrompt,
        companyName: jobData.company,
        jobTitle: jobData.title,
        jobUrl: jobData.url
      });
    }

    return NextResponse.json(
      { error: "Invalid document type" },
      { status: 400 }
    );

  } catch (error) {
    console.error("Error in extension generate API:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

// Helper function to format cover letter from structured data
function formatCoverLetter(data: any): string {
  if (!data) return '';

  const sections = [];

  if (data.greeting) {
    sections.push(data.greeting);
  }

  if (data.opening_paragraph) {
    sections.push(data.opening_paragraph);
  }

  if (data.body_paragraphs && Array.isArray(data.body_paragraphs)) {
    sections.push(...data.body_paragraphs);
  } else if (data.body_paragraph) {
    sections.push(data.body_paragraph);
  }

  if (data.closing_paragraph) {
    sections.push(data.closing_paragraph);
  }

  if (data.sign_off) {
    sections.push(data.sign_off);
  }

  return sections.join('\n\n');
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