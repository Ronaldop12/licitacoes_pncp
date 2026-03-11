"""
Carregar alertas do JSON para o banco de dados SQLite
"""
import json
import sqlite3
from alerts_db import AlertasDB

# Carregar config
with open('config/alertas_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Inicializar DB
db = AlertasDB()

# Limpar alertas existentes
conn = db._get_connection()
cursor = conn.cursor()
cursor.execute("DELETE FROM alertas")
conn.commit()

# Carregar alertas do JSON
alertas = config.get('alertas', [])
for alerta_cfg in alertas:
    try:
        ufs_str = json.dumps(alerta_cfg.get('ufs', []))
        orgaos_str = json.dumps(alerta_cfg.get('orgaos', ['*']))
        palavras_str = json.dumps(alerta_cfg.get('palavras_chave', []))
        
        cursor.execute("""
            INSERT INTO alertas (
                nome, chat_id, ufs, valor_min, valor_max,
                orgaos, palavras_chave, ativo, frequencia_min,
                criado_em, ultimo_alerta, proxximo_alerta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alerta_cfg['nome'],
            alerta_cfg['chat_id'],
            ufs_str,
            alerta_cfg.get('valor_min', 0),
            alerta_cfg.get('valor_max', 999999999),
            orgaos_str,
            palavras_str,
            1 if alerta_cfg.get('ativo', True) else 0,
            alerta_cfg.get('frequencia_min', 60),
            alerta_cfg.get('criado_em', ''),
            alerta_cfg.get('ultimo_alerta'),
            alerta_cfg.get('proxximo_alerta', ''),
        ))
        print(f"✓ Alerta carregado: {alerta_cfg['nome']}")
    except Exception as e:
        print(f"✗ Erro ao carregar {alerta_cfg.get('nome')}: {e}")

conn.commit()
conn.close()

# Verificar
alertas_db = db.listar_alertas(apenas_ativos=True)
print(f"\nTotal de alertas ativos no banco: {len(alertas_db)}")
for alerta in alertas_db:
    print(f"  - {alerta['nome']} (UF: {alerta.get('ufs')})")
