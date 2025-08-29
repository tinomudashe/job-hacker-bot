import { NextRequest, NextResponse } from "next/server";
import { auth, currentUser } from "@clerk/nextjs/server";
import jwt from "jsonwebtoken";

// This endpoint allows logged-in users to get a temporary token for the extension
export async function GET(request: NextRequest) {
  try {
    // Get the current session
    const session = await auth();
    
    if (!session || !session.userId) {
      return NextResponse.json(
        { error: "Not authenticated" },
        { status: 401 }
      );
    }

    // Get user details
    const user = await currentUser();
    
    if (!user) {
      return NextResponse.json(
        { error: "User not found" },
        { status: 404 }
      );
    }

    // Create a temporary JWT token that the extension can use
    // This token will be valid for 24 hours
    const tempToken = jwt.sign(
      {
        userId: session.userId,
        email: user.emailAddresses[0]?.emailAddress,
        firstName: user.firstName,
        lastName: user.lastName,
        imageUrl: user.imageUrl,
        type: 'session_bridge',
        exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60) // 24 hours
      },
      process.env.CLERK_SECRET_KEY || 'fallback-secret',
      { algorithm: 'HS256' }
    );

    return NextResponse.json({
      success: true,
      token: tempToken,
      user: {
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.emailAddresses[0]?.emailAddress,
        profileImage: user.imageUrl
      }
    });

  } catch (error) {
    console.error("Error generating extension token:", error);
    return NextResponse.json(
      { error: "Failed to generate token" },
      { status: 500 }
    );
  }
}

// Allow CORS for extension
export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}