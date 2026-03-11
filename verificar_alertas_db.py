"""Verificar alertas no banco de dados"""
from alerts_db import AlertasDB

db = AlertasDB()
alertas = db.listar_alertas(apenas_ativos=True)

print(f"\nTotal de alertas ativos: {len(alertas)}\n")
for a in alertas:
    print(f"ID: {a['id']} | Nome: {a['nome']}")
    print(f"  UF: {a.get('ufs')}")
    print(f"  Chat ID: {a['chat_id']}")
    print()
