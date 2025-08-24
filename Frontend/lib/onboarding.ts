import { cookies } from 'next/headers';

export async function checkOnboardingStatus(token: string): Promise<boolean> {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/onboarding/status`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      console.error('Failed to fetch onboarding status:', response.status);
      return false;
    }

    const data = await response.json();
    const isCompleted = data.onboarding_completed || false;
    
    // Set a cookie with the onboarding status (expires in 1 hour)
    if (isCompleted) {
      cookies().set('onboarding_verified', 'true', {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60, // 1 hour
        path: '/',
      });
    }
    
    return isCompleted;
  } catch (error) {
    console.error('Error checking onboarding status:', error);
    return false;
  }
}