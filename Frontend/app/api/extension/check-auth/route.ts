import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

export async function GET(request: NextRequest) {
  try {
    // Check if this is an extension request
    const isExtensionRequest = request.headers.get('X-Extension-Request') === 'true';
    
    if (!isExtensionRequest) {
      return NextResponse.json(
        { error: "Invalid request source" },
        { status: 400 }
      );
    }

    // Get the session from Clerk
    const session = await auth();
    
    if (!session || !session.userId) {
      return NextResponse.json({
        authenticated: false,
        message: "No active session"
      });
    }

    // Get the session token that can be used for API calls
    // This will be the user's Clerk session JWT token
    const sessionToken = session.sessionId ? `clerk_${session.sessionId}` : null;

    // Get user details from Clerk
    const { clerkClient } = await import("@clerk/nextjs/server");
    const user = await clerkClient.users.getUser(session.userId);

    return NextResponse.json({
      authenticated: true,
      userId: session.userId,
      sessionToken: sessionToken,
      user: {
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.emailAddresses[0]?.emailAddress,
        profileImage: user.imageUrl
      },
      message: "User is authenticated"
    });

  } catch (error) {
    console.error("Error checking authentication:", error);
    return NextResponse.json(
      { 
        authenticated: false,
        error: "Failed to check authentication" 
      },
      { status: 500 }
    );
  }
}

// Add CORS headers for extension access
export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-Extension-Request',
      'Access-Control-Allow-Credentials': 'true',
    },
  });
}