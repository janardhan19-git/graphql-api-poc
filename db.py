import os
from dotenv import load_dotenv
from azure.cosmos import CosmosClient, PartitionKey, exceptions

# Load environment variables from .env file
load_dotenv()

# ----------------------------
# Cosmos DB Config
# ----------------------------
COSMOS_URI = os.getenv("COSMOS_URI")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

# Initialize Cosmos Client
client = CosmosClient(COSMOS_URI, credential=COSMOS_KEY)

# Ensure database exists
database = client.create_database_if_not_exists(DATABASE_NAME)

# Ensure container exists
container = database.create_container_if_not_exists(
    id=CONTAINER_NAME,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400
)
