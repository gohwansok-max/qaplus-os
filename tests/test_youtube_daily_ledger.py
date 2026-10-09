import ast
import base64
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'daily_qa_autopilot.py'
module = ast.parse(SOURCE.read_text(encoding='utf-8'))
helper = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == '_persist_daily_upload_entry')
ns = {'os': os, 'json': json}
exec(compile(ast.Module(body=[helper], type_ignores=[]), str(SOURCE), 'exec'), ns)

class Response:
    def __init__(self, status, data=None): self.status_code, self.data = status, data
    def json(self): return self.data

class LedgerTests(unittest.TestCase):
    def invoke(self, fake, entry):
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'true','GH_TOKEN':'test-only','GITHUB_REPOSITORY':'owner/repo','GITHUB_REF_NAME':'main','GITHUB_RUN_ID':'123'}), patch.dict(sys.modules, {'requests':fake}), patch('time.sleep'):
            ns['_persist_daily_upload_entry']('2026-10-09', entry)
    def test_reserve_missing(self):
        writes=[]
        fake=types.SimpleNamespace(get=lambda *a,**k:Response(404),put=lambda *a,**k:(writes.append(k['json']) or Response(201)))
        entry={'status':'uploading','privacy_status':'private','run_id':'123'}
        self.invoke(fake,entry)
        data=json.loads(base64.b64decode(writes[0]['content']))
        self.assertEqual(data['uploads']['2026-10-09'],entry)
    def test_other_run_blocks(self):
        data={'sha':'abc','content':base64.b64encode(json.dumps({'uploads':{'2026-10-09':{'run_id':'456','video_id':'existing'}}}).encode()).decode()}
        fake=types.SimpleNamespace(get=lambda *a,**k:Response(200,data),put=lambda *a,**k:self.fail('must not write'))
        with self.assertRaisesRegex(RuntimeError,'Another run'):
            self.invoke(fake,{'run_id':'123'})
    def test_same_run_result_and_retry(self):
        data={'sha':'abc','content':base64.b64encode(json.dumps({'uploads':{'2026-10-09':{'run_id':'123','status':'uploading'}}}).encode()).decode()}
        statuses=iter([409,200]); writes=[]
        fake=types.SimpleNamespace(get=lambda *a,**k:Response(200,data),put=lambda *a,**k:(writes.append(k['json']) or Response(next(statuses))))
        self.invoke(fake,{'run_id':'123','video_id':'verified','privacy_status':'private','status':'uploaded'})
        self.assertEqual(len(writes),2)
        self.assertEqual(writes[-1]['sha'],'abc')

if __name__=='__main__': unittest.main()
