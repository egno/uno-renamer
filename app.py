from requests import get, post, patch
from dotenv import load_dotenv
import os
import re

load_dotenv()

APP_API_URL = os.getenv('APP_API_URL')
APP_USER = os.getenv('APP_USER')
APP_PASSWD = os.getenv('APP_PASSWD')
IMAGE_PATH = os.getenv('IMAGE_PATH','/opt/data/images')
PART_SIZE = os.getenv('PART_SIZE', 4)
CONN_TIMEOUT = os.getenv('CONN_TIMEOUT', 5)


def login():
    res = post(f'{APP_API_URL}/rpc/login',
               data={
                   'login': APP_USER,
                   'pass': APP_PASSWD
               },
               timeout=CONN_TIMEOUT
               )
    return res.json()[0].get('token')


def headers(token):
    return {
        'Authorization': f'Bearer {token}',
        'Prefer': 'count=exact',
        'Accept': 'application/json'
    }


def getList(token, query):
    res = get(
        f'{APP_API_URL}{query}',
        headers=headers(token),
        timeout=CONN_TIMEOUT
    )
    rng = res.headers['Content-Range']
    # print(rng)
    cnt = None
    last = None
    if rng is not None:
        m = re.search(r'^([^-]*)-?(.*)/(.*)$', rng)
        try:
            cnt = int(m.group(3))
        except:
            pass
        try:
            last = int(m.group(2))
        except:
            pass
    return res.json(), last, cnt


def saveBusiness(token, id, j):
    print(f'      SAVE: {id} {j.get("avatar")}')
    res = patch(
        f'{APP_API_URL}/business?id=eq.{id}',
        headers=headers(token),
        json={
            'j': j
        }
    )
    return res.status_code == 204


def branches(token):
    res = get(
        f'{APP_API_URL}/business?type=is.null&j->>avatar=not.eq.id&select=id,type,j->>avatar',
        headers=headers(token),
        timeout=CONN_TIMEOUT
    )
    return res.json()


def processBusiness(token, business):
    id = business.get('id', '')
    print(f' PROCESS: {id}')

    if id == '':
        print(f'  NO business: {id}')
        return

    new_avatar = f'{id}.png'
    avatar = business.get('j', {}).get('avatar', '')
    j = business['j']

    if avatar == '' and os.path.isfile(f'{IMAGE_PATH}/{new_avatar}'):
        avatar = new_avatar

    if os.path.isfile(f'{IMAGE_PATH}/{avatar}') and avatar != new_avatar:
        print(f'  FILE rename: {avatar} to {new_avatar}')
        os.replace(
            f'{IMAGE_PATH}/{avatar}', f'{IMAGE_PATH}/{new_avatar}'
        )

    doBusinessBranches(token, business)

    if os.path.isfile(f'{IMAGE_PATH}/{new_avatar}'):
        print(f'Exists: {IMAGE_PATH}/{new_avatar}')
        j['avatar'] = new_avatar
    else:
        print(f'Not exists: {IMAGE_PATH}/{new_avatar}')
        del j['avatar']

    saveBusiness(token, id, j)


def processBusinessBranch(token, business, branch, force=False):
    business_avatar = f'{business.get("id")}.png'
    branch_avatar = f'{branch.get("id")}.png'
    old_business_avatar = business.get("j", {}).get('avatar', '')
    old_avatar = branch.get("j", {}).get('avatar', '')

    if (old_avatar == '' or old_avatar == old_business_avatar or old_avatar == business_avatar):
        if os.path.isfile(f'{IMAGE_PATH}/{business_avatar}') \
                and (not os.path.isfile(f'{IMAGE_PATH}/{branch_avatar}') or force):
            print(f'   LINK: {business_avatar} to file {branch_avatar}')
            os.system(
                f'ln -s {IMAGE_PATH}/{business_avatar} {IMAGE_PATH}/{branch_avatar}'
            )
    else:
        if os.path.isfile(f'{IMAGE_PATH}/{old_avatar}'):
            print(f'   FILE rename: {old_avatar} to {branch_avatar}')
            os.replace(
                f'{IMAGE_PATH}/{old_avatar}', f'{IMAGE_PATH}/{branch_avatar}'
            )

    j = branch['j']
    j['avatar'] = branch_avatar
    saveBusiness(token, branch.get("id"), j)


def doBusinessBranches(token, business, force=False):
    cur = 0
    cnt = None
    while cnt is None or (cur is not None and cnt > cur):
        query = f'/business?select=id,j&type=is.null&parent=eq.{business.get("id")}&order=id&limit={PART_SIZE}&offset={cur}'
        l, cur, cnt = getList(token, query)
        if cur is not None:
            cur += 1
            print(f' > branches of {business.get("id")}: {cur} / {cnt}')
            if cnt is None:
                break
            for branch in l:
                processBusinessBranch(token, business, branch, force)


def doBusinesses(token):
    cur = 0
    cnt = None
    while cnt is None or (cur is not None and cnt > cur):
        query = f'/business?select=id,j&type=eq.C&j->>avatar=not.is.null&order=id&limit={PART_SIZE}&offset={cur}'
        l, cur, cnt = getList(token, query)
        if cur is not None:
            cur += 1
            print(f'> Companies: {cur} / {cnt}')
            for business in l:
                processBusiness(token, business)
                pass


def doBranches(token):
    cur = 0
    cnt = None
    while cnt is None or (cur is not None and cnt > cur):
        query = f'/business?select=id,j&type=is.null&j->>avatar=not.is.null&order=id&limit={PART_SIZE}&offset={cur}'
        l, cur, cnt = getList(token, query)
        if cur is not None:
            cur += 1
            print(f'> Branches: {cur} / {cnt}')
            for business in l:
                processBusiness(token, business)



def main():
    token = login()
    print('== COMPANIES ==')
    doBusinesses(token)
    # print('== BRANCHES ==')
    # doBranches(token)


main()
