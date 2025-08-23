import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

// Define public routes that don't require authentication
const isPublicRoute = createRouteMatcher([
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/',
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
  
  // Skip public routes except root when authenticated
  if (isPublicRoute(req) && pathname !== '/') {
    return NextResponse.next()
  }

  const { userId, sessionClaims } = auth()
  
  // If not authenticated, Clerk will handle the redirect
  if (!userId) {
    // Allow access to public routes
    if (isPublicRoute(req)) {
      return NextResponse.next()
    }
    return
  }

  // Check if user has completed onboarding
  const publicMetadata = sessionClaims?.publicMetadata as { onboardingCompleted?: boolean } | undefined
  const onboardingCompleted = publicMetadata?.onboardingCompleted || false

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