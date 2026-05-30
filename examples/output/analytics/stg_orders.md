# Cleaned Orders

> **Technical model:** `stg_orders`  ·  **Table:** `"warehouse"."analytics"."stg_orders"`

## Description
Cleaned order records.

## Business Context
| Key | Value |
| --- | --- |
| label | Cleaned Orders |

## Upstream Lineage
<!-- LINEAGE_SUMMARY -->
Cleaned Orders is built directly from the raw Source Orders feed, which is loaded into the warehouse from the source system. It is the first, lightly cleaned layer on top of that raw order data.
<!-- /LINEAGE_SUMMARY -->

**Direct sources:** Source Orders

## What This Model Does
<!-- TRANSFORMATION_SUMMARY -->
This model takes the raw order records and standardizes them, keeping each order's identifier, the customer who placed it, and the order amount ready for downstream use.
<!-- /TRANSFORMATION_SUMMARY -->

## Columns
| Column | Type | Description | Tests | Meta |
| --- | --- | --- | --- | --- |
| order_id | integer | Surrogate key for an order. | — | — |
| customer_id | integer | Customer who placed the order. | relationships (to: ref('stg_customers'), field: customer_id) | — |
| amount | numeric | Order amount in USD. | — | — |

## Tests Applied (model level)
- assert_positive_amount

---
*Generated from dbt artifacts (schema: https://schemas.getdbt.com/dbt/manifest/v12.json).*
