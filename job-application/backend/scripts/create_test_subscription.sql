-- Update subscription for test user
UPDATE subscriptions 
SET plan = 'premium',
    status = 'active',
    stripe_customer_id = 'cus_STmgqLFiHHveK6',
    stripe_subscription_id = 'sub_test'
WHERE user_id = (SELECT id FROM users WHERE email = 'test@example.com');

-- If no subscription exists, create one
INSERT INTO subscriptions (id, user_id, plan, status, stripe_customer_id, stripe_subscription_id)
SELECT 
    gen_random_uuid(),
    users.id,
    'premium',
    'active',
    'cus_STmgqLFiHHveK6',
    'sub_test'
FROM users 
WHERE email = 'test@example.com'
AND NOT EXISTS (
    SELECT 1 FROM subscriptions WHERE user_id = users.id
); 