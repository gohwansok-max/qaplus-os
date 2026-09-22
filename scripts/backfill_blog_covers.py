#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""대표 이미지 누락·플레이스홀더 글 7건을 안전하게 갱신한다."""
import os
import requests
from blogger_publisher import get_access_token

BASE = 'https://raw.githubusercontent.com/gohwansok-max/qaplus-os/main/outputs/2026/09/22/images/'
COVERS = {
 '1658306629647491085': 'imagegen-jcL6a8nNUP7mwRnu.png',
 '4497068911862520923': 'imagegen-jteHe3xUK38nrlZb.png',
 '5412794638766236493': 'imagegen-pzE18RvMzgxCRqst.png',
 '2498805336860286030': 'imagegen-pdojgcWaZmNwPMkW.png',
 '3498074541996391093': 'imagegen-Q14imGKozeAy3FXM.png',
 '3390185052145291804': 'imagegen-CztYvG0CjIbtvFEg.png',
 '3890610529954911832': 'imagegen-a6PIPnMOSxqCd6an.png',
}

def main():
 token=get_access_token(); blog=os.environ.get('BLOGGER_BLOG_ID')
 if not token or not blog: raise RuntimeError('Blogger credentials missing')
 h={'Authorization':f'Bearer {token}','Content-Type':'application/json'}
 for pid,name in COVERS.items():
  url=f'https://www.googleapis.com/blogger/v3/blogs/{blog}/posts/{pid}'
  r=requests.get(url,params={'view':'ADMIN'},headers=h,timeout=30); r.raise_for_status(); post=r.json()
  src=BASE+name; body=post.get('content','')
  if src in body: print(f'[SKIP] {pid}'); continue
  if 'IMAGE_PLACEHOLDER_1' in body: body=body.replace('IMAGE_PLACEHOLDER_1',src)
  else:
   tag=f'<img class="qa-cover" src="{src}" alt="{post.get("title","QA PLUS 대표 이미지")} 대표 이미지" />'
   body=tag+body
  payload={'title':post['title'],'content':body}
  if post.get('labels'): payload['labels']=post['labels']
  u=requests.put(url,headers=h,json=payload,timeout=60); u.raise_for_status(); print(f'[OK] {pid}')

if __name__ == '__main__': main()































