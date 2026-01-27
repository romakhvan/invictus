SELECT COUNT(DISTINCT us.user) as users_count
FROM mongo.usersubscriptions as us
JOIN mongo.subscriptions as s ON us.subscription_id = s.id
WHERE s.club_id = '675bd789dbd381003eb9f649'
  AND us.is_deleted = false
    AND us.is_active = true
    and us.created_at > '2025-01-01'