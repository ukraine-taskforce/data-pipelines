import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from datetime import datetime
from pyspark.sql.functions import explode
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv,
                          ["JOB_NAME",
                           "bucket"])
bucket = args["bucket"]
table_name = "Requests"
read_percentage = "0.2"
output_location = f's3://{bucket}/requests-aggregated'

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

requests = glueContext.create_dynamic_frame.from_options("dynamodb",
                                                  connection_options={
                                                                      "dynamodb.input.tableName": table_name,
                                                                      "dynamodb.throughput.read.percent": read_percentage,
                                                                      "dynamodb.splits": "100"
                                                                      }
                                                ).toDF()

requests_exploded = requests.withColumn("categoryId", explode(requests.body.supplies))

requests_exploded.createOrReplaceTempView("requests_exploded")

result = spark.sql("select to_date(to_timestamp(timestamp / 1000)) as date, body.location as city_id, categoryId as category_id, sum(peopleCount) as requested_amount from requests_exploded group by to_date(to_timestamp(timestamp / 1000)), body.location, categoryId")

result.repartition(1).write.mode("overwrite").format("json").save(output_location)
