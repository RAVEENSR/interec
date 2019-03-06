from pyspark.sql import SparkSession

spark = SparkSession \
    .builder \
    .master('local') \
    .appName("Interec") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

all_prs_df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/rails") \
    .option("driver", 'com.mysql.cj.jdbc.Driver')\
    .option("dbtable", "pull_request") \
    .option("user", "root") \
    .option("password", "") \
    .load()

all_integrators_df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/rails") \
    .option("driver", 'com.mysql.cj.jdbc.Driver')\
    .option("dbtable", "integrator") \
    .option("user", "root") \
    .option("password", "") \
    .load()

all_prs_df.createOrReplaceTempView("pull_requests")
all_integrators_df.createOrReplaceTempView("integrators")
