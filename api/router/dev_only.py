from fastapi import APIRouter
from dbconnect import connect_server, delete_docs

router = APIRouter()

# TODO: add OAuth to this endpoint
@router.get('/delete-all/{collection}', response_model=None, tags=['dev-only'], status_code=410)
async def delete_all_docs(collection: str):
  client = await connect_server()
  await delete_docs(client, {}, collection, single=False)
  return {"message": f"All documents in {collection} have been successfully deleted!"}