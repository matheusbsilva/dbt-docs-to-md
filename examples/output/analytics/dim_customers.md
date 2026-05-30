# Customers

> **Technical model:** `dim_customers`  ·  **Table:** `"warehouse"."analytics"."dim_customers"`

## Description
One row per customer enriched with lifetime order totals.

## Business Context
| Key | Value |
| --- | --- |
| domain | marketing |
| label | Customers |
| owner | analytics-team |

## Upstream Lineage
<!-- LINEAGE_SUMMARY -->
Customers is built directly from two cleaned data sets — Cleaned Customers and Cleaned Orders. Those, in turn, come from the raw feeds Source Customers and Source Orders that land in the warehouse from the operational systems. In other words, this is the customer-level view assembled on top of the cleaned customer and order data.
<!-- /LINEAGE_SUMMARY -->

**Direct sources:** Cleaned Customers, Cleaned Orders

## What This Model Does
<!-- TRANSFORMATION_SUMMARY -->
This model produces one row per customer. It matches each customer to their orders, adds up the value of all their orders to calculate a lifetime value, and labels customers who have spent more than $1,000 as "vip" and everyone else as "standard". Customers with no orders are still included, with a lifetime value of nothing. It powers the Total Lifetime Value and Customer Count metrics.
<!-- /TRANSFORMATION_SUMMARY -->

## Columns
| Column | Type | Description | Tests | Meta |
| --- | --- | --- | --- | --- |
| customer_id | integer | Unique identifier of the customer. | not_null, unique | — |
| email | varchar | Customer email address. | — | pii: True |
| lifetime_value | numeric | Total amount the customer has spent. | — | — |
| status | varchar | Customer status. | accepted_values (values: vip, standard) | — |

## Semantic Model
### Customers
Customer-level semantic model for self-serve analytics.
_Primary entity:_ `customer`

**Entities** (how this data joins to other models)

| Entity | Type | Description |
| --- | --- | --- |
| Customer | primary | The customer. |

**Dimensions** (ways to slice the metrics)

| Dimension | Type | Description |
| --- | --- | --- |
| Customer Status | categorical | VIP or standard tier. |
| Signup Date | time | When the customer signed up. |

**Measures** (the quantities that can be aggregated)

| Measure | Aggregation | Description |
| --- | --- | --- |
| Lifetime Value | sum | Total spend per customer. |
| Customer Count | count_distinct | Number of distinct customers. |

## Metrics You Can Measure
**Available metrics:** Total Lifetime Value, Customer Count

| Metric | Type | How it's calculated | Description |
| --- | --- | --- | --- |
| Total Lifetime Value | simple | lifetime_value | The total amount spent across all customers. |
| Customer Count | simple | customer_count | The number of distinct customers. |

---
*Generated from dbt artifacts (schema: https://schemas.getdbt.com/dbt/manifest/v12.json).*
