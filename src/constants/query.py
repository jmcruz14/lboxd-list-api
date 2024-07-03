'''This Python script serves as the conversion layer of API calls from the Nuxt/JS
layer of the app to the FastAPI portion of the app.'''

# def match_array(key: str, vals: list[str]) -> dict:
  
def agg_ops_dict(measure: str, key: str | list, vals: list | None = None) -> dict | bool:
  '''
    Fetches the equivalent MongoDB aggregate function based on request payload.
    
    Parameters:
      measure (str): the aggregate measure to be used\n
      key (str): document field to be used for aggregation\n
      vals (list, optional): list of values to be parsed
    
    Returns:
      dict
  '''
  # v1.0 support: $avg, $add
  try:
    if measure == 'mean':
      return { 
        "$group": {
          "_id": None,
          'avgQty': { "$avg": "$" + key }
        }
      }
    if measure == 'sum':
      return { '$group': {
        "_id": None,
        'totalSum': { "$sum": key }}
      } 
    
    else:
      raise Exception
  except Exception as e:
    print(f"error noticed {e}")
    return False