# Databricks notebook source
# MAGIC %md
# MAGIC # SmartLive - Silver ETL
# MAGIC
# MAGIC Notebook này làm sạch dữ liệu, flatten cột `analysis`,
# MAGIC loại bản ghi trùng và repartition để xử lý song song tốt hơn trên cluster.

# COMMAND ----------

import json

from pyspark.sql import functions as F
from pyspark.sql import Window


def get_widget(name: str, default: str) -> str:
    dbutils.widgets.text(name, default)
    value = dbutils.widgets.get(name).strip()
    return value or default


bronze_table = get_widget("bronze_table", "main.default.smartlive_sync_comments_bronze")
silver_table = get_widget("silver_table", "main.default.smartlive_sync_comments_silver")
target_partitions = int(get_widget("target_partitions", "8"))

spark.conf.set("spark.sql.shuffle.partitions", str(max(1, target_partitions)))

bronze_df = spark.table(bronze_table)

window_spec = Window.partitionBy("platform", "source_comment_id").orderBy(F.col("synced_at").desc())

silver_df = (
    bronze_df.withColumn("event_ts", F.to_timestamp("synced_at"))
    .withColumn("event_date", F.to_date("event_ts"))
    .withColumn("intent", F.col("analysis.intent"))
    .withColumn("sentiment", F.col("analysis.sentiment"))
    .withColumn("lead_score", F.col("analysis.lead_score").cast("int"))
    .withColumn("priority", F.col("analysis.priority"))
    .withColumn("row_num", F.row_number().over(window_spec))
    .filter(F.col("row_num") == 1)
    .drop("row_num")
    .repartition(max(1, target_partitions), "platform", "event_date")
)

(
    silver_df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(silver_table)
)

row_count = silver_df.count()

display(
    silver_df.select(
        "sync_record_id",
        "platform",
        "event_date",
        "intent",
        "sentiment",
        "lead_score",
        "priority",
        "sync_status",
    ).orderBy(F.col("event_ts").desc())
)

summary = {
    "step": "silver_etl",
    "source_table": bronze_table,
    "target_table": silver_table,
    "row_count": row_count,
    "target_partitions": target_partitions,
}

print(f"Transformed {row_count} rows into {silver_table}")
dbutils.notebook.exit(json.dumps(summary))
