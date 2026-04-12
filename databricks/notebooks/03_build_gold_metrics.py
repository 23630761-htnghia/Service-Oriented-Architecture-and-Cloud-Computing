# Databricks notebook source
# MAGIC %md
# MAGIC # SmartLive - Gold Metrics
# MAGIC
# MAGIC Notebook này tổng hợp KPI hằng ngày theo nền tảng để phục vụ báo cáo
# MAGIC và minh chứng phần Delta Lake / pipeline trên Databricks.

# COMMAND ----------

import json

from pyspark.sql import functions as F


def get_widget(name: str, default: str) -> str:
    dbutils.widgets.text(name, default)
    value = dbutils.widgets.get(name).strip()
    return value or default


silver_table = get_widget("silver_table", "main.default.smartlive_sync_comments_silver")
gold_table = get_widget("gold_table", "main.default.smartlive_daily_metrics_gold")

silver_df = spark.table(silver_table)

gold_df = (
    silver_df.groupBy("event_date", "platform")
    .agg(
        F.count("*").alias("total_comments"),
        F.sum(F.when(F.col("sync_status") == "synced", F.lit(1)).otherwise(F.lit(0))).alias("synced_comments"),
        F.sum(F.when(F.col("sync_status") == "analysis_failed", F.lit(1)).otherwise(F.lit(0))).alias("failed_comments"),
        F.sum(F.when(F.col("priority") == "high", F.lit(1)).otherwise(F.lit(0))).alias("high_priority_comments"),
        F.round(F.avg("lead_score"), 2).alias("average_lead_score"),
        F.countDistinct("account_id").alias("active_accounts"),
        F.collect_set("intent").alias("intents_seen"),
        F.collect_set("sentiment").alias("sentiments_seen"),
    )
    .orderBy("event_date", "platform")
)

(
    gold_df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(gold_table)
)

row_count = gold_df.count()

display(gold_df)

summary = {
    "step": "gold_reporting",
    "source_table": silver_table,
    "target_table": gold_table,
    "row_count": row_count,
}

print(f"Built {row_count} aggregated rows into {gold_table}")
dbutils.notebook.exit(json.dumps(summary))
