"""Script temporário para corrigir mojibake em pncp_radar_ti_plus.py"""

with open('pncp_radar_ti_plus.py', 'r', encoding='utf-8') as f:
    content = f.read()

# UTF-8 double-encoding: bytes were read as Latin-1 then re-encoded as UTF-8
mapping = {
    '\u00c3\u0087': 'Ç',
    '\u00c3\u0095': 'Õ',
    '\u00c3\u00a1': 'á',
    '\u00c3\u00a3': 'ã',
    '\u00c3\u00a7': 'ç',
    '\u00c3\u00b5': 'õ',
    '\u00c3\u00ba': 'ú',
    '\u00c3\u00a9': 'é',
    '\u00c3\u00ad': 'í',
    '\u00c3\u00b3': 'ó',
    '\u00c3\u00b4': 'ô',
    '\u00c3\u00aa': 'ê',
    '\u00c3\u0081': 'Á',
    '\u00c3\u0089': 'É',
    '\u00c3\u008d': 'Í',
    '\u00c3\u0093': 'Ó',
    '\u00c3\u009a': 'Ú',
    '\u00c3\u0082': 'Â',
    '\u00c3\u00a2': 'â',
    '\u00c3\u00bc': 'ü',
    '\u00c3\u00b1': 'ñ',
}

fixed = content
for bad, good in mapping.items():
    fixed = fixed.replace(bad, good)

count_before = content.count('\u00c3')
count_after = fixed.count('\u00c3')
print(f'Mojibake chars before: {count_before}, after: {count_after}')

with open('pncp_radar_ti_plus.py', 'w', encoding='utf-8') as f:
    f.write(fixed)

print('File fixed successfully')
