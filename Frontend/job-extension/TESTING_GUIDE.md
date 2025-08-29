# Chrome Extension Testing Guide

## Installation Steps

1. **Open Chrome Extensions Page**
   - Navigate to `chrome://extensions/`
   - Or click menu → More tools → Extensions

2. **Enable Developer Mode**
   - Toggle "Developer mode" switch in the top right corner

3. **Load the Extension**
   - Click "Load unpacked"
   - Navigate to `/Frontend/job-extension/dist`
   - Select the `dist` folder and click "Select"

4. **Verify Installation**
   - Extension should appear in your extensions list
   - Job Hacker Bot logo should be visible in the toolbar
   - Pin the extension for easy access

## Testing Checklist

### 1. Initial Setup
- [ ] Extension loads without errors
- [ ] Popup opens when clicking extension icon
- [ ] UI matches your app's light mode design
- [ ] Logo displays correctly

### 2. Settings & Authentication

#### Option A: Extension Token
- [ ] Click Settings icon (gear) in extension
- [ ] In your main app, go to Settings → Chrome Extension Access
- [ ] Generate a new token
- [ ] Copy token and paste in extension settings
- [ ] Verify token shows green checkmark
- [ ] Save token
- [ ] Token status shows in header (green key icon)

#### Option B: Sign In
- [ ] Click "Sign in to Job Hacker Bot" link
- [ ] Complete sign-in process
- [ ] Return to extension

### 3. Job Extraction Testing

Test on these sites:
- [ ] **LinkedIn**: https://www.linkedin.com/jobs/
  - Navigate to any job posting
  - Click "Extract Job Details"
  - Verify job title, company, location extracted

- [ ] **Indeed**: https://www.indeed.com/
  - Search for jobs and open a listing
  - Extract details
  - Check all fields populated

- [ ] **Glassdoor**: https://www.glassdoor.com/Job/
  - Open job posting
  - Test extraction

- [ ] **Generic Site**: Any company careers page
  - Test smart detection

### 4. Document Generation

#### Cover Letter Generation
- [ ] After extracting job, click "Create Cover Letter"
- [ ] If using token: Should proceed directly
- [ ] If no auth: Should prompt for token/sign-in
- [ ] Verify API call succeeds
- [ ] App opens with PDF dialog
- [ ] Cover letter content is generated
- [ ] Company name and job title pre-filled

#### Resume Tailoring
- [ ] Click "Tailor Resume"
- [ ] Similar flow as cover letter
- [ ] PDF dialog opens with resume data

### 5. Error Handling
- [ ] Test with no internet connection
- [ ] Test with expired token
- [ ] Test on non-job pages
- [ ] Verify error messages are helpful

### 6. Connection Status
- [ ] Green "Connected" when app is running
- [ ] Red "Disconnected" when app is not running
- [ ] Token indicator shows when token is saved

## Troubleshooting

### Extension Not Loading
1. Check console for errors: Right-click popup → Inspect
2. Verify all files in `dist` folder
3. Rebuild if needed: `npm run build`

### Authentication Issues
1. Verify token starts with `jhb_`
2. Check token hasn't expired
3. Ensure app backend is running
4. Try generating a new token

### Job Extraction Not Working
1. Make sure you're on a job details page (not search results)
2. Check console for extraction errors
3. Some sites may have changed their structure

### API Errors
1. Check app is running on correct port (default: 3000)
2. Verify backend is running (port 8000)
3. Check network tab in developer tools
4. Ensure CORS is properly configured

## Development Mode

For development with hot reload:
```bash
cd /Frontend/job-extension
npm run dev
```

After changes:
1. Go to chrome://extensions/
2. Click "Reload" on the extension
3. Test your changes

## Backend Requirements

Ensure these are running:
1. **Frontend App**: `npm run dev` (port 3000)
2. **Backend API**: `python main.py` (port 8000)
3. **Database**: PostgreSQL should be running

## Testing Different Scenarios

1. **First-time user**: No token, no session
2. **Returning user with token**: Token saved
3. **Signed-in user**: Active session in app
4. **Expired token**: Token expired after X days
5. **Multiple tabs**: Extension working across tabs

## Success Criteria

✅ Extension installs without errors
✅ Can extract job data from major sites
✅ Authentication works (token or sign-in)
✅ Cover letters generate successfully
✅ PDF dialog opens with content
✅ UI is responsive and matches app design
✅ Error messages are clear and helpful

## Notes

- Extension tokens are separate from API keys
- Tokens can be revoked in app settings
- Each token tracks last used time
- Generated content uses your existing resume data
- All API calls go through your backend