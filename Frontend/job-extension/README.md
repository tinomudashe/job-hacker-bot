# Job Hacker Bot Chrome Extension

A Chrome extension that extracts job details from any website and generates tailored CVs and cover letters using the Job Hacker Bot platform.

## Features

- 🔍 **Smart Job Extraction**: Automatically extracts job details from popular job sites like LinkedIn, Indeed, Glassdoor, and more
- 📝 **One-Click Cover Letters**: Generate personalized cover letters based on the job description
- 📄 **Resume Tailoring**: Customize your resume to match specific job requirements
- 🎨 **Matching Design**: UI matches the main Job Hacker Bot app for a consistent experience
- 🔐 **Secure Integration**: Uses your existing Job Hacker Bot account

## Installation

### Building the Extension

1. Install dependencies:
```bash
cd job-extension
npm install
```

2. Build the extension:
```bash
npm run build
```

This will create a `dist` folder with the built extension.

### Loading in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked"
4. Select the `dist` folder from the build step
5. The extension will appear in your extensions bar

## Development

For development with hot reload:
```bash
npm run dev
```

This will watch for changes and rebuild automatically. You'll need to refresh the extension in Chrome after changes.

## Usage

1. **Navigate to a Job Posting**: Go to any job listing on supported sites
2. **Click the Extension Icon**: Click the Job Hacker Bot icon in your browser toolbar
3. **Extract Job Details**: Click "Extract Job Details" to pull information from the page
4. **Generate Documents**: Choose either:
   - "Create Cover Letter" - Generates a tailored cover letter
   - "Tailor Resume" - Customizes your resume for the position
5. **Review & Download**: The app will open with the PDF dialog showing your generated content

## Supported Sites

The extension works best with:
- LinkedIn Jobs
- Indeed
- Glassdoor
- Greenhouse.io
- Lever.co
- Workday
- AngelList/Wellfound
- Most company career pages

For other sites, it uses smart detection to find job details.

## Configuration

The extension connects to your Job Hacker Bot app running at `http://localhost:3000` by default. 

To use with the production app, update the `appUrl` in the extension settings.

## Permissions

The extension requires:
- **activeTab**: To read job details from the current page
- **storage**: To save extracted job data temporarily
- **tabs**: To open the Job Hacker Bot app

## Troubleshooting

### Extension Not Extracting Data
- Make sure you're on a job listing page (not a search results page)
- Try refreshing the page and extracting again
- Check if the site is supported in the console logs

### Connection Issues
- Ensure the Job Hacker Bot app is running
- Check if you're signed in to the app
- Verify the app URL in extension settings

### Generated Content Not Appearing
- Make sure you're signed in to Job Hacker Bot
- Check that you have an active subscription
- Ensure your resume is set up in the app

## Development Notes

### Tech Stack
- React 18 with TypeScript
- Tailwind CSS (matching app styles)
- Webpack for bundling
- Chrome Extension Manifest V3

### API Integration
The extension communicates with the Job Hacker Bot backend through:
- `/api/health` - Connection check
- `/api/extension/generate` - Content generation
- URL parameters for triggering the PDF dialog

### Key Files
- `src/popup/App.tsx` - Main extension UI
- `src/content/index.ts` - Content script for data extraction
- `src/background/index.ts` - Background service worker
- `public/manifest.json` - Extension configuration

## Contributing

When adding support for new job sites:
1. Add extraction logic to `extractDataFromPage()` in `App.tsx`
2. Test on multiple job listings from that site
3. Handle edge cases (missing fields, different layouts)

## License

Part of the Job Hacker Bot platform. All rights reserved.