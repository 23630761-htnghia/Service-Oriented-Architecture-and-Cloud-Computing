# Databricks notebook source
# MAGIC %md
# MAGIC # SmartLive - Bronze Ingestion
# MAGIC
# MAGIC Notebook này nạp file JSON export từ `sync-service` hoặc file mẫu trong repo,
# MAGIC sau đó ghi xuống bảng Delta bronze để làm đầu vào cho các bước ETL tiếp theo.

# COMMAND ----------

import json

from pyspark.sql import functions as F


def get_widget(name: str, default: str) -> str:
    dbutils.widgets.text(name, default)
    value = dbutils.widgets.get(name).strip()
    return value or default


input_path = get_widget("input_path", "dbfs:/FileStore/smartlive/raw/sync_records_sample.json")
bronze_table = get_widget("bronze_table", "main.default.smartlive_sync_comments_bronze")
shuffle_partitions = int(get_widget("shuffle_partitions", "8"))
schema_name = ".".join(bronze_table.split(".")[:2]) if bronze_table.count(".") >= 2 else "default"

spark.conf.set("spark.sql.shuffle.partitions", str(max(1, shuffle_partitions)))
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

raw_df = (
    spark.read.option("multiline", "true")
    .json(input_path)
    .withColumn("ingested_at", F.current_timestamp())
    .withColumn("source_file", F.input_file_name())
)

bronze_df = raw_df.select(
    "sync_record_id",
    "source",
    "source_comment_id",
    "platform",
    "account_id",
    "livestream_id",
    "username",
    "comment",
    "synced_at",
    "sync_status",
    "error_detail",
    "analysis",
    "ingested_at",
    "source_file",
)

(
    bronze_df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(bronze_table)
)

row_count = bronze_df.count()

display(bronze_df.orderBy(F.col("synced_at").desc()))

summary = {
    "step": "bronze_ingestion",
    "input_path": input_path,
    "target_table": bronze_table,
    "row_count": row_count,
    "shuffle_partitions": shuffle_partitions,
}

print(f"Loaded {row_count} rows into {bronze_table}")
dbutils.notebook.exit(json.dumps(summary))
