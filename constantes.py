"""
Constantes compartilhadas entre módulos do Radar de Licitações TI.
Centraliza PALAVRAS_TI e PALAVRAS_EXCLUSAO para evitar imports circulares.
"""

# Palavras-chave de TI
PALAVRAS_TI = [
    "software", "sistema de informa", "tecnologia da informa",
    "informática", "desenvolvimento de sistema",
    "cloud", "nuvem", "computação em nuvem",
    "aplicativo", "licença de software", "licenciamento de software",
    "infraestrutura de ti", "infraestrutura de rede",
    "segurança da informação", "cibersegurança",
    "banco de dados", "python", "java", "nodejs",
    "docker", "kubernetes", "aws", "azure", "gcp",
    "erp", "lgpd", "data center", "datacenter",
    "firewall", "antivírus", "backup",
    "helpdesk", "suporte técnico de ti",
    "cabeamento estruturado", "rede lógica",
    "inteligência artificial", "machine learning",
    "devops", "microsserviço", "saas", "iaas", "paas",
    "business intelligence", "bi ", "analytics",
    "computador", "notebook", "servidor",
    "storage", "switch", "roteador", "access point",
    "no-break", "nobreak", "ups",
    "videoconferência", "voip",
    "certificação digital", "assinatura digital",
    "governança de ti", "itil", "cobit",
]

# Palavras que geram falso positivo (excluir)
PALAVRAS_EXCLUSAO = [
    "rede de esgoto", "rede de água", "rede elétrica",
    "rede de proteção", "dados epidemiológico", "dados cadastr",
    "sistema de esgoto", "sistema viário", "sistema de drenagem",
    "infraestrutura viária", "infraestrutura urbana",
]
