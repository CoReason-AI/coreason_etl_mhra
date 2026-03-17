{{ config(
    materialized='table'
) }}

with parsed_substances as (
    select
        coreason_id,
        licence_number,
        active_substances_raw,
        -- Replace potential multiple delimiters (commas, slashes, semicolons) with a uniform delimiter first
        -- Since the spec says "separated by commas or slashes", let's use regexp_split_to_table
        unnest(
            string_to_array(
                regexp_replace(active_substances_raw, '[,;/]', '|', 'g'),
                '|'
            )
        ) as active_substance
    from {{ ref('mhra_approved_products') }}
    where active_substances_raw is not null
)

select
    coreason_id,
    licence_number,
    trim(active_substance) as active_substance
from parsed_substances
where trim(active_substance) != ''
