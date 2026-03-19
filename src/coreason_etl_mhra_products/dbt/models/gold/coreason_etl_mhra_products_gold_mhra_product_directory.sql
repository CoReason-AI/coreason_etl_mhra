{{ config(
    materialized='table'
) }}

select
    coreason_id,
    licence_number,
    content_hash,
    product_name,
    active_substances_raw,
    mah_name,
    licence_route,
    authorisation_date,
    status
from {{ ref('coreason_etl_mhra_products_silver_mhra_approved_products') }}
where status = 'Granted'
