from fastapi import APIRouter
from routes.dbconnect import connect_server, delete_docs

admin_route = APIRouter()

# TODO: add OAuth to this endpoint
@admin_route.get('/delete-all/{collection}', response_model=None, tags=['dev-only'], status_code=410)
async def delete_all_docs(collection: str):
  client = await connect_server()
  await delete_docs(client, {}, collection, single=False)
  return {"message": f"All documents in {collection} have been successfully deleted!"}