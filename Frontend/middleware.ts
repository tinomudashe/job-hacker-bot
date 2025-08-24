import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

// Define public routes that don't require authentication
const isPublicRoute = createRouteMatcher([
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/webhook(.*)',
])

// Define onboarding route
const isOnboardingRoute = createRouteMatcher(['/onboarding(.*)'])

// Define protected routes that require onboarding completion
const requiresOnboarding = createRouteMatcher([
  '/dashboard(.*)',
  '/profile(.*)',
  '/settings(.*)',
  '/admin(.*)',
])

export default clerkMiddleware(async (auth, req) => {
  const { pathname } = req.nextUrl
  
  // Allow public routes
  if (isPublicRoute(req)) {
    return NextResponse.next()
  }

  const { userId, getToken } = auth()
  
  // If not authenticated, Clerk will handle the redirect
  if (!userId) {
    return
  }

  // Check for cookies that indicate onboarding status
  const cookies = req.headers.get('cookie') || ''
  const hasVerifiedCookie = cookies.includes('onboarding_verified=true')
  const hasTemporaryCookie = cookies.includes('onboarding_completed_temp=true')
  
  // If we have a verified cookie or temporary cookie, user has completed onboarding
  let onboardingCompleted = hasVerifiedCookie || hasTemporaryCookie
  
  // If no verified cookie and not on onboarding page, check the database
  if (!onboardingCompleted && !isOnboardingRoute(req)) {
    try {
      const token = await getToken()
      if (token) {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const response = await fetch(`${apiUrl}/api/users/onboarding/status`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })
        
        if (response.ok) {
          const data = await response.json()
          onboardingCompleted = data.onboarding_completed || false
          
          // Set cookie if onboarding is completed
          if (onboardingCompleted) {
            const res = NextResponse.next()
            res.cookies.set('onboarding_verified', 'true', {
              httpOnly: true,
              secure: process.env.NODE_ENV === 'production',
              sameSite: 'lax',
              maxAge: 60 * 60, // 1 hour
              path: '/',
            })
            return res
          }
        }
      }
    } catch (error) {
      console.error('Error checking onboarding status:', error)
    }
  }

  // Special handling for root path - redirect to onboarding if not completed
  if (pathname === '/' && !onboardingCompleted) {
    const onboardingUrl = new URL('/onboarding', req.url)
    return NextResponse.redirect(onboardingUrl)
  }

  // If user hasn't completed onboarding and is trying to access protected routes
  if (!onboardingCompleted && requiresOnboarding(req)) {
    const onboardingUrl = new URL('/onboarding', req.url)
    return NextResponse.redirect(onboardingUrl)
  }

  // If user has completed onboarding and is trying to access onboarding page
  if (onboardingCompleted && isOnboardingRoute(req)) {
    const homeUrl = new URL('/', req.url)
    return NextResponse.redirect(homeUrl)
  }

  return NextResponse.next()
})

export const config = {
  matcher: [
    // Skip Next.js internals and all static files
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
} 