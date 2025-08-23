# Userback Feedback Integration Setup

This guide explains how to set up and configure Userback for collecting user feedback in Job Hacker Bot.

## What is Userback?

Userback is a visual feedback and bug reporting tool that allows users to:
- Report bugs with automatic screenshots
- Request new features
- Provide general feedback
- Include console logs and network data for debugging
- Annotate screenshots to highlight issues

## Setup Instructions

### 1. Create a Userback Account

1. Go to [https://userback.io](https://userback.io) and sign up for an account
2. Choose a plan (they offer a free tier for small projects)

### 2. Create a New Project

1. After logging in, create a new project
2. Name it "Job Hacker Bot" or similar
3. Select "Web Application" as the project type

### 3. Get Your Access Token

1. In your Userback dashboard, go to **Settings** → **Widget**
2. Find your **Access Token** (it looks like: `UB-xxxxxxxxxx`)
3. Copy this token

### 4. Configure Environment Variables

Add the following to your `.env.local` file:

```env
# Required: Your Userback access token
NEXT_PUBLIC_USERBACK_TOKEN=UB-your-token-here

# Optional: Enable in development (defaults to production only)
NEXT_PUBLIC_ENABLE_USERBACK=true
```

### 5. Customize Widget Settings (Optional)

The widget is pre-configured with sensible defaults, but you can customize it in `/components/userback-widget.tsx`:

#### Position
- `bottom_right` (default)
- `bottom_left`
- `top_right`
- `top_left`
- `center`

#### Style
- `circle` (default) - Circular feedback button
- `rectangle` - Rectangular button
- `text` - Text-only button

#### Colors
Change `accent_color` to match your brand (currently set to `#3B82F6`)

#### Categories
Modify the feedback categories:
```javascript
categories: [
  { name: 'Bug Report', value: 'bug' },
  { name: 'Feature Request', value: 'feature' },
  { name: 'General Feedback', value: 'general' },
  { name: 'UI/UX Improvement', value: 'ui_ux' },
]
```

### 6. Userback Dashboard Configuration

In your Userback dashboard:

1. **Integrations**: Connect to your project management tools
   - Jira
   - Trello
   - Slack
   - GitHub Issues
   - Linear
   - And more...

2. **Team Members**: Invite team members to receive and manage feedback

3. **Email Notifications**: Configure who receives feedback notifications

4. **Custom Fields**: Add custom fields to collect specific information

## Features Implemented

### Automatic User Information
When a user is logged in via Clerk, the widget automatically captures:
- User email
- User name
- User ID
- Account creation date

### Feedback Types
Users can submit:
- **Bug Reports** - With screenshots and console logs
- **Feature Requests** - New functionality ideas
- **General Feedback** - Any other feedback
- **UI/UX Improvements** - Design and usability suggestions

### Data Collection
Each feedback submission includes:
- Screenshot capability
- Console logs (for debugging)
- Network logs (API calls)
- Browser information
- Page URL
- User session data

### Priority Levels
Users can set priority:
- Low
- Medium
- High
- Critical

## Testing the Integration

1. Start your development server:
   ```bash
   npm run dev
   ```

2. Look for the feedback widget in the bottom-right corner

3. Click the widget to open the feedback form

4. Submit test feedback

5. Check your Userback dashboard to see the submission

## Production Deployment

The widget is configured to run in production by default. Make sure to:

1. Set `NEXT_PUBLIC_USERBACK_TOKEN` in your production environment variables
2. The widget will automatically load for all users in production
3. Monitor feedback in your Userback dashboard

## Troubleshooting

### Widget Not Appearing

1. Check console for errors
2. Verify `NEXT_PUBLIC_USERBACK_TOKEN` is set correctly
3. In development, ensure `NEXT_PUBLIC_ENABLE_USERBACK=true` is set
4. Check browser console for "Userback widget loaded successfully" message

### User Data Not Captured

1. Ensure user is logged in via Clerk
2. Check that Clerk integration is working properly
3. Verify user object is available in the component

### Feedback Not Submitting

1. Check network tab for failed requests
2. Verify your Userback project is active
3. Check Userback dashboard for any project limits

## Best Practices

1. **Respond to Feedback**: Acknowledge user feedback promptly
2. **Close the Loop**: Let users know when their reported issues are fixed
3. **Categorize Properly**: Use categories to organize feedback
4. **Set Up Integrations**: Connect to your project management tools
5. **Monitor Regularly**: Check dashboard daily for new feedback

## Support

- Userback Documentation: [https://support.userback.io](https://support.userback.io)
- Userback Support: support@userback.io
- Job Hacker Bot Issues: Create an issue in your repository