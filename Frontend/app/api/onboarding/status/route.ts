import { auth } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

// Force this route to be dynamic (not statically rendered)
export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const { userId, getToken } = auth();
    
    if (!userId) {
      return NextResponse.json({ onboardingCompleted: false });
    }

    const token = await getToken();
    
    if (!token) {
      return NextResponse.json({ onboardingCompleted: false });
    }

    // Call backend to check onboarding status
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/onboarding/status`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      console.error('Failed to fetch onboarding status:', response.status);
      return NextResponse.json({ onboardingCompleted: false });
    }

    const data = await response.json();
    
    return NextResponse.json({
      onboardingCompleted: data.onboarding_completed || false,
      cvUploaded: data.cv_uploaded || false,
    });
  } catch (error) {
    console.error('Error checking onboarding status:', error);
    return NextResponse.json({ onboardingCompleted: false });
  }
}