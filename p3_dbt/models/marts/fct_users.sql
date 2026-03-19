-- On s'appuie sur le staging qu'on a créé juste avant
WITH users AS (
    SELECT * FROM {{ ref('stg_users') }}
)

SELECT
    city,
    COUNT(user_id) AS total_users
FROM users
GROUP BY 1
ORDER BY total_users DESC