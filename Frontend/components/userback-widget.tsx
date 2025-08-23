'use client';

import { useEffect } from 'react';
import { useUser } from '@clerk/nextjs';

interface UserbackConfig {
  token: string;
  email?: string;
  name?: string;
  custom_data?: Record<string, any>;
}

export function UserbackWidget() {
  const { user } = useUser();

  useEffect(() => {
    // Only load Userback in production or if explicitly enabled
    const shouldLoadUserback = process.env.NEXT_PUBLIC_USERBACK_TOKEN && 
                               (process.env.NODE_ENV === 'production' || 
                                process.env.NEXT_PUBLIC_ENABLE_USERBACK === 'true');
    
    if (!shouldLoadUserback) {
      console.log('Userback is disabled in this environment');
      return;
    }

    // Prevent loading multiple times
    if (window.Userback) {
      console.log('Userback already loaded');
      return;
    }

    // Load Userback script
    window.Userback = window.Userback || {};
    
    // Configure Userback with user data if available
    if (user) {
      window.Userback.email = user.primaryEmailAddress?.emailAddress || '';
      window.Userback.name = user.fullName || `${user.firstName || ''} ${user.lastName || ''}`.trim();
      window.Userback.custom_data = {
        user_id: user.id,
        created_at: user.createdAt,
        has_image: !!user.imageUrl,
      };
    }

    // Set the access token
    window.Userback.access_token = process.env.NEXT_PUBLIC_USERBACK_TOKEN!;
    
    // Additional configuration options
    window.Userback.widget_settings = {
      language: 'en',
      position: 'bottom_right', // Options: bottom_right, bottom_left, top_right, top_left, center
      style: 'circle', // Options: circle, rectangle, text
      trigger_type: 'click', // Options: click, hover
      device_type: 'both', // Options: desktop, mobile, both
      autohide: false,
      accent_color: '#3B82F6', // Matches your primary color
      
      // Feedback categories
      categories: [
        { name: 'Bug Report', value: 'bug' },
        { name: 'Feature Request', value: 'feature' },
        { name: 'General Feedback', value: 'general' },
        { name: 'UI/UX Improvement', value: 'ui_ux' },
      ],
      
      // Custom fields for feedback form
      custom_fields: [
        {
          name: 'priority',
          label: 'Priority',
          type: 'select',
          required: false,
          options: ['Low', 'Medium', 'High', 'Critical']
        },
        {
          name: 'page_url',
          label: 'Page URL',
          type: 'text',
          required: false,
          default_value: window.location.href
        }
      ],
      
      // Feedback form settings
      feedback_form: {
        email_required: !user, // Only require email if user is not logged in
        rating_enabled: true,
        screenshot_enabled: true,
        attachment_enabled: true,
        console_log_enabled: true, // Capture console logs
        network_log_enabled: true, // Capture network requests
      },
      
      // Widget text customization
      widget_text: {
        trigger_text: 'Feedback',
        title: 'Send us feedback',
        description: 'Help us improve Job Hacker Bot',
        submit_button: 'Send Feedback',
        success_message: 'Thank you for your feedback!',
        email_placeholder: 'Your email address',
        message_placeholder: 'Describe your feedback, bug report, or feature request...',
      }
    };

    // Create and append the Userback script
    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://static.userback.io/widget/v1.js';
    script.onload = () => {
      console.log('Userback widget loaded successfully');
      
      // Initialize Userback after script loads
      if (window.Userback && window.Userback.init) {
        window.Userback.init();
      }
    };
    script.onerror = () => {
      console.error('Failed to load Userback widget');
    };

    document.head.appendChild(script);

    // Cleanup function
    return () => {
      // Remove the script when component unmounts
      const existingScript = document.querySelector('script[src="https://static.userback.io/widget/v1.js"]');
      if (existingScript) {
        existingScript.remove();
      }
    };
  }, [user]);

  return null; // This component doesn't render anything visible
}

// Type declarations for TypeScript
declare global {
  interface Window {
    Userback: any;
  }
}