# Data Catalog Index

Business-readable documentation for every dbt model in the project, organized by layer.

See the [Metrics Glossary](metrics.md) for the 2 metric(s) available in the semantic layer.

## analytics

| Model | Description | Documentation |
| --- | --- | --- |
| Cleaned Customers (`stg_customers`) | Cleaned customer records from the raw ingestion layer. | [View](analytics/stg_customers.md) |
| Cleaned Orders (`stg_orders`) | Cleaned order records. | [View](analytics/stg_orders.md) |
| Customers (`dim_customers`) | One row per customer enriched with lifetime order totals. | [View](analytics/dim_customers.md) |

*Total models: 3. Generated from dbt schema: https://schemas.getdbt.com/dbt/manifest/v12.json.*
