WITH source_data AS (
    SELECT * FROM {{ source('api_source', 'raw_users') }}
)

SELECT
    id AS user_id,
    name AS user_name,
    email,
    -- On extrait les infos du JSON imbriqué (BigQuery gère ça avec le point)
    address.city AS city,
    company.name AS company_name
FROM source_data