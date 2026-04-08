import json

with open('credentials.json', 'r', encoding='utf-8') as f:
    creds = json.load(f)

creds_str = json.dumps(creds)

with open('.env', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    line = line.strip()
    if not line or line.startswith('#'):
        new_lines.append(line)
        continue
    
    if '=' in line:
        k, v = line.split('=', 1)
        k = k.strip()
        if k == 'GOOGLE_SHEETS_CREDENTIALS':
            continue
        new_lines.append(f'{k}={v}')

# We need the creds wrapped in three single quotes so it perfectly handles newlines and nested double quotes in TOML.
# Actually, TOML supports multiline strings with `'''`.
formatted_creds = json.dumps(creds, indent=2)

new_lines.append("GOOGLE_SHEETS_CREDENTIALS='''")
new_lines.append(formatted_creds)
new_lines.append("'''")

with open('.env', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines) + '\n')
