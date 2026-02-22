import json

with open('data/experiment/user_group_map.json') as f:
    groups = json.load(f)

with open('data/test_users.json') as f:
    users = json.load(f)

print('前5个用户分组:')
for u in users[:5]:
    gid = str(u['user_id'])
    group = groups.get(gid, '未分组')
    print(f'  {u["username"]} (ID: {gid}) -> {group}')