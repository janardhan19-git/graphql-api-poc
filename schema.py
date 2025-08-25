import strawberry
from db import container
from models import User

@strawberry.type
class Query:
    @strawberry.field
    def get_user(self, id: str) -> User | None:
        try:
            item = container.read_item(item=id, partition_key=id)
            return User(id=item["id"], name=item["name"], email=item["email"])
        except:
            return None

    @strawberry.field
    def list_users(self) -> list[User]:
        users = []
        for item in container.read_all_items():
            users.append(User(id=item["id"], name=item["name"], email=item["email"]))
        return users


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, id: str, name: str, email: str) -> User:
        user_data = {"id": id, "name": name, "email": email}
        container.upsert_item(user_data)
        return User(**user_data)


schema = strawberry.Schema(query=Query, mutation=Mutation)
