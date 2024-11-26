from gql import gql, Client
import src.config as config
from gql.transport.requests import RequestsHTTPTransport
from src.gql import gql_query
import os
import copy
from src.tool import get_current_timestamp

empty_notifies = {
    "id": None,
    "lrt": 0,
    "notifies": [],
}

gql_member_notifiers = '''
query Members($where: MemberWhereInput!){
  members(where: $where){
    id
    customId
    name
    avatar
  }
}
'''

gql_notify_member = '''
query Member{{
  member(where: {{id: {ID} }}){{
    id
    customId
    name
    avatar
  }}
}}
'''

gql_notify_story = '''
query Story{{
  story(where: {{id: {ID} }}){{
    id
    title
    url
    source{{
      id
      customId
      title
    }}
    commentCount(where: {{is_active: {{equals: true}} }})
  }}
}}
'''

gql_notify_comment = '''
query Comment{{
  comment(where: {{id: {ID} }}){{
    id
    content
  }}
}}
'''

gql_notify_collection = '''
query Collection{{
  collection(where: {{id: {ID} }}){{
    id
    title
  }}
}}
'''

def get_objective_content(gql_client, objective, targetId):
    content = None
    if objective=="story":
        gql_string = gql_notify_story.format(ID=targetId)
        data = gql_client.execute(gql(gql_string))
        content = data['story']
    if objective=="comment":
        gql_string = gql_notify_comment.format(ID=targetId)
        data = gql_client.execute(gql(gql_string))
        content = data['comment']        
    if objective=="collection":
        gql_string = gql_notify_collection.format(ID=targetId)
        data = gql_client.execute(gql(gql_string))
        content = data['collection'] 
    return content

def get_notifies(db, memberId: str, index: int=0, take: int=10):
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    col_notify = db.notifications
    record = col_notify.find_one(memberId)
    
    empty_template = copy.deepcopy(empty_notifies)
    empty_template["id"] = memberId
    if record is None:
        col_notify.insert_one(empty_template)
        return empty_template     
    
    response = empty_template
    try:
        lrt = record.get('lrt', 0)
        all_notifies = record.get('notifies', [])
        all_notifies = all_notifies[index: index+take]

        # collect from_members information
        notifiersId = []
        targetObjs = {}
        for notify in all_notifies:
            action = notify['action']
            if action in config.PAYMENT_NOTIFIES:
              continue
            aggregate = notify['aggregate']
            membersId = notify['from']
            if aggregate==False:
                notifiersId.append(membersId)
            else:
                notifiersId.extend(membersId[:config.MAX_AVATAR_DISPLAYED])
            objective = notify['objective']
            targetId = notify['targetId']
            targetId_list = targetObjs.setdefault(objective, [])
            targetId_list.append(targetId)
        notifiersId = list(set(notifiersId))

        # search member's full information
        mutation = {
            "where": {
                "id": {
                    "in": notifiersId
                }
            }
        }
        members, _ = gql_query(MESH_GQL_ENDPOINT, gql_member_notifiers, mutation)
        members = members['members']
        member_table = {}
        for member in members:
            id = member['id']
            member_table[id] = member

        # generate the full notifies information
        full_notifies = []
        gql_transport = RequestsHTTPTransport(url=MESH_GQL_ENDPOINT)
        gql_client = Client(transport=gql_transport, fetch_schema_from_transport=True)
        for notify in all_notifies:
            action = notify['action']
            if action in config.PAYMENT_NOTIFIES:
              full_notifies.append(notify)
              continue
            aggregate = notify["aggregate"]
            from_notifiers = notify["from"]
            objective = notify['objective']
            targetId = notify['targetId']
            len_notifiers = len(from_notifiers) if aggregate==True else 1
            
            notifiers = []
            if aggregate==True:
                notifiersId = from_notifiers[:config.MAX_AVATAR_DISPLAYED]
                for notifierId in notifiersId:
                    notifier = member_table.get(notifierId, None)
                    if notifier:
                        notifiers.append(notifier)
            else:
                notifier = member_table.get(from_notifiers, None)
                if notifier:
                    notifiers.append(notifier)
                else:
                    print(f"cannot get memberId: {memberId}")
            full_notify = {
                "uuid": notify["uuid"],
                "read": notify["read"],
                "action": notify["action"],
                "objective": objective,
                "targetId": targetId,
                "aggregate": aggregate,
                "notifiers_num": len_notifiers,
                "notifiers": notifiers,
                "ts": notify["ts"]
            }
            content = get_objective_content(gql_client, objective, targetId) # get content information about the objective targetId
            if content:
                full_notify['content'] = content
            
            full_notifies.append(full_notify)
            response = {
                "id": memberId,
                "lrt": lrt,
                "notifies": full_notifies
            }
    except Exception as e:
        print("get_notifies error: ", e)
    return response