from fastapi import FastAPI, Depends
from strawberry.fastapi import GraphQLRouter
from schema import schema
from auth import auth_dependency, graphql_context_getter

app = FastAPI(title="GraphQL + CosmosDB (Secured)")

graphql_app = GraphQLRouter(
    schema,
    context_getter=graphql_context_getter,
    graphiql=True 
)
# Require auth for all GraphQL operations
app.include_router(
    graphql_app, prefix="/graphql", dependencies=[Depends(auth_dependency)]
)

@app.get("/")
def root():
    return {"message": "Go to /graphql (auth required)"}
