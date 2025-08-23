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

export default clerkMiddleware((auth, req) => {
  const { pathname } = req.nextUrl
  
  // Allow public routes
  if (isPublicRoute(req)) {
    return NextResponse.next()
  }

  const { userId, sessionClaims } = auth()
  
  // If not authenticated, Clerk will handle the redirect
  if (!userId) {
    return
  }

  // Check if user has completed onboarding
  const publicMetadata = sessionClaims?.publicMetadata as { onboardingCompleted?: boolean } | undefined
  const onboardingCompleted = publicMetadata?.onboardingCompleted || false
  
  // Check for temporary cookie that indicates onboarding was just completed
  const cookies = req.headers.get('cookie') || ''
  const hasTemporaryOnboardingFlag = cookies.includes('onboarding_completed_temp=true')

  // Log for debugging
  console.log('Middleware check:', {
    pathname,
    userId,
    onboardingCompleted,
    publicMetadata,
    hasTemporaryOnboardingFlag
  })

  // Special handling for root path - redirect to onboarding if not completed
  if (pathname === '/' && !onboardingCompleted && !hasTemporaryOnboardingFlag) {
    // Check if we're coming from onboarding (to prevent redirect loop)
    const referer = req.headers.get('referer')
    if (referer && referer.includes('/onboarding')) {
      console.log('Coming from onboarding, allowing access to home')
      return NextResponse.next()
    }
    
    const onboardingUrl = new URL('/onboarding', req.url)
    return NextResponse.redirect(onboardingUrl)
  }

  // If user hasn't completed onboarding and is trying to access protected routes
  if (!onboardingCompleted && !hasTemporaryOnboardingFlag && requiresOnboarding(req)) {
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