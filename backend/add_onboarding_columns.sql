-- Add onboarding_completed and onboarding_completed_at columns to users table if they don't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE NOT NULL;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMP WITH TIME ZONE;

-- Update existing users who have onboarding completed in preferences
UPDATE users 
SET onboarding_completed = TRUE,
    onboarding_completed_at = NOW()
WHERE preferences LIKE '%"onboarding_completed": true%'
   OR preferences LIKE '%"onboarding_completed":true%';