# Cleaned Customers

> **Technical model:** `stg_customers`  ·  **Table:** `"warehouse"."analytics"."stg_customers"`

## Description
Cleaned customer records from the raw ingestion layer.

## Business Context
| Key | Value |
| --- | --- |
| label | Cleaned Customers |

## Upstream Lineage
<!-- LINEAGE_SUMMARY -->
Cleaned Customers is built directly from the raw Source Customers feed, which is loaded into the warehouse from the source system. It is the first, lightly cleaned layer on top of that raw data.
<!-- /LINEAGE_SUMMARY -->

**Direct sources:** Source Customers

## What This Model Does
<!-- TRANSFORMATION_SUMMARY -->
This model takes the raw customer records and standardizes them, keeping each customer's identifier and email address ready for downstream use.
<!-- /TRANSFORMATION_SUMMARY -->

## Columns
| Column | Type | Description | Tests | Meta |
| --- | --- | --- | --- | --- |
| customer_id | integer | Surrogate key for a customer. | — | — |
| email | varchar | Customer email address. | — | pii: True |

---
*Generated from dbt artifacts (schema: https://schemas.getdbt.com/dbt/manifest/v12.json).*
