{{ config(
    materialized='table'
) }}

with raw as (
    select
        coreason_id,
        ingestion_ts,
        raw_data,
        md5(raw_data::text) as content_hash
    from {{ source('bronze', 'coreason_etl_mhra_products_bronze_mhra_products_raw') }}
),

parsed as (
    select
        coreason_id,
        ingestion_ts,
        content_hash,
        -- Clean Licence Number: strip leading/trailing whitespace
        trim(raw_data->>'Licence Number') as licence_number,
        raw_data->>'Product Name' as product_name,
        raw_data->>'Active Substance' as active_substances_raw,
        raw_data->>'Marketing Authorisation Holder' as mah_name,
        raw_data->>'Licence Route' as licence_route,

        -- Parse to Date handling basic variations if necessary,
        -- assuming format allows native parsing or standard TO_DATE.
        -- We'll cast the string to date (assuming format like YYYY-MM-DD or standard ISO).
        -- If format is tricky, might need to_date(..., '...')
        cast(raw_data->>'Date of Authorisation' as date) as authorisation_date,

        raw_data->>'Status' as status
    from raw
),

deduplicated as (
    select
        *,
        row_number() over (partition by licence_number order by ingestion_ts desc) as rn
    from parsed
)

select
    coreason_id,
    content_hash,
    licence_number,
    product_name,
    active_substances_raw,
    mah_name,
    licence_route,
    authorisation_date,
    status
from deduplicated
where rn = 1
