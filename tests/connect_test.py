# import asyncio
# import unittest
# import dbconnect as db

# class TestConnect(unittest.TestCase):
#   # check connection
#   async def setUp(self):
#     self.client = await db.connect_server()
  
#   async def tearDown(self):
#     self.client.close()
  
#   async def test_ok_connection(self):
#     self.assertNotEqual(self.client.admin.command("ping")["ok"], 0.0, "Connection not okay")
  
#   async def test_query_db(self):
#     query = {}
#     collection = 'list_history'
#     results = await db.query_db(self.client, query, collection)
#     self.assertIsInstance(results, list, "Query did not return a list")

# if __name__ == '__main__':
#   asyncio.run(unittest.main())

# def test_