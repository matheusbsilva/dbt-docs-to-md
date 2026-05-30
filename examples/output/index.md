# Data Catalog Index

Business-readable documentation for every dbt model in the project.

See the [Metrics Glossary](metrics.md) for the 2 metric(s) available in the semantic layer.

| Model | Description | Documentation |
| --- | --- | --- |
| Cleaned Customers (`stg_customers`) | Cleaned customer records from the raw ingestion layer. | [View](cleaned-customers.md) |
| Cleaned Orders (`stg_orders`) | Cleaned order records. | [View](cleaned-orders.md) |
| Customers (`dim_customers`) | One row per customer enriched with lifetime order totals. | [View](customers.md) |

*Total models: 3. Generated from dbt schema: https://schemas.getdbt.com/dbt/manifest/v12.json.*
