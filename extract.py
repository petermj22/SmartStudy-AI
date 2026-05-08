import json
for line in open(r'C:\\Users\\suhel\\.gemini\\antigravity\\brain\\67e8c789-bce5-4979-8b88-04140603ae55\\.system_generated\\logs\\overview.txt', encoding='utf-8'):
  try:
    data=json.loads(line)
    if 'content' in data and 'file:///e:/SmartStudy-AI/frontend/app.py' in data['content']:
      print('FOUND')
      open('old_app.txt', 'a', encoding='utf-8').write(data['content'])
  except:
    pass
