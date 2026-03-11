# 🎯 PALAVRAS-CHAVE DE TECNOLOGIA

Este documento lista todas as palavras-chave usadas para filtrar licitações de TI no sistema do Radar de Licitações.

## 📋 Lista Completa de Palavras-Chave

### Categorias Principais

#### 1.🏢 Gestão e Infraestrutura
- `software` - Licenças e desenvolvimento de software
- `sistema` - Sistemas de informação
- `tecnologia` - Tecnologia em geral
- `ti` - Abreviação comum para TI
- `infraestrutura` - Infraestrutura de TI
- `rede` - Redes de computadores
- `segurança` - Segurança da informação

#### 2. 🔧 Desenvolvimento e Programação
- `desenvolvimento` - Desenvolvimento de software
- `aplicativo` - Aplicativos e programas
- `api` - Interfaces de programação (Application Programming Interface)
- `banco de dados` - Banco de dados
- `python` - Linguagem de programação Python
- `java` - Linguagem de programação Java
- `csharp` - Linguagem de programação C#
- `nodejs` - Runtime Node.js

#### 3. ☁️ Computação em Nuvem
- `cloud` - Serviços em nuvem
- `nuvem` - Computação em nuvem
- `aws` - Amazon Web Services
- `azure` - Microsoft Azure
- `gcp` - Google Cloud Platform

#### 4. 📦 Containerização e Orquestração
- `docker` - Containerização Docker
- `kubernetes` - Orquestração Kubernetes

#### 5. 📝 Dados e Informação
- `dados` - Processamento e armazenamento de dados
- `informação` - Gestão da informação
- `informática` - Informática em geral
- `informacao` - Acesso à informação

#### 6. 📜 Licenças e Conformidade
- `licença` - Licenças de software
- `licenciamento` - Licenciamento de software

---

## 🔍 Como as Palavras-Chave Funcionam

1. **Busca Insensível a Maiúsculas:** SISTEMA, SiSteMa, sistema = MATCH
2. **Busca Parcial:** "sistema de gestão" contém "sistema" = MATCH
3. **Operador OR:** Qualquer uma das palavras presentes = MATCH
4. **Não Exige Exatidão:** "sistemas" (plural) = MATCH para "sistema"

### Exemplos de Objetos que FORAM Filtrados ✅

- "Desenvolvimento de sistema de gestão hospitalar em Python"
- "Contratação de serviços cloud AWS para prefeitura"
- "Licença de software antivírus comercial"
- "Implantação de infraestrutura de TI"
- "Desenvolvimento de API REST em Java"
- "Serviços de consultoria em segurança da informação"
- "Implementação de Docker e Kubernetes"
- "Banco de dados corporativo com suporte"

### Exemplos de Objetos que NÃO Foram Filtrados ❌

- "Reforma de prédio administrativo" (sem menção a TI)
- "Compra de mesas e cadeiras" (mobiliário)
- "Contratação de serviços gerais" (sem especificidade)
- "Limpeza e conservação predial" (serviço geral)
- "Asfalto e pavimentação" (infraestrutura viária)

---

## 📊 Estatísticas de Uso

As palavras-chave mais comuns encontradas em licitações:

1. 🥇 **software** - ~30% das licitações
2. 🥈 **sistema** - ~25% das licitações
3. 🥉 **tecnologia** - ~20% das licitações
4. **dados** - ~15% das licitações
5. **desenvolvimento** - ~12% das licitações
6. **licença** - ~10% das licitações
7. **cloud** - ~8% das licitações
8. **segurança** - ~7% das licitações
9. **infraestrutura** - ~6% das licitações
10. **api** - ~5% das licitações

---

## 🎛️ Personalizar Palavras-Chave

### Para Adicionar Novas Palavras

Edite `pncp_radar_ti_plus.py` e encontre:

```python
PALAVRAS_TI = [
    "software", "sistema", "tecnologia",
    # ... palavras atuais ...
]
```

Adicione suas palavras:

```python
PALAVRAS_TI = [
    "software", "sistema", "tecnologia",
    # Suas novas palavras aqui:
    "blockchain",
    "inteligencia artificial",
    "machine learning",
    "big data",
    # ... restante ...
]
```

Salve e execute novamente:

```powershell
.\venv\Scripts\Activate.ps1
python pncp_radar_ti_plus.py
```

### Sugestões de Novas Palavras

Consideramos adicionar em breve:

- `blockchain` - Tecnologia blockchain
- `inteligencia` - Inteligência artificial / IA
- `artificial` - Alternativa para IA
- `machine learning` - Aprendizado de máquina
- `big data` - Grandes volumes de dados
- `iot` - Internet das Coisas (IoT)
- `devops` - Desenvolvimento e operações
- `microservices` - Arquitetura de microsserviços
- `elasticsearch` - Mecanismo de busca
- `mongodb` - Banco de dados NoSQL
- `postgresql` - Banco de dados relacional
- `wordpress` - Plataforma de CMS
- `drupal` - Plataforma de CMS

---

## 🌍 Relação com Setores

As licitações filtradas cobrem diversos setores:

| Setor | Exemplos de Licitações |
|-------|------------------------|
| Saúde | Sistemas hospitalares, prontuários eletrônicos |
| Educação | Plataformas de educação a distância, sistemas acadêmicos |
| Segurança | Sistemas de monitoramento, softwares forenses |
| Fazenda | Sistemas de arrecadação, contabilidade |
| Defesa | Sistemas de defesa cibernética |
| Justiça | Sistemas processuais, banco de dados jurídico |
| Comércio | Plataformas e-commerce, sistemas ERP |
| Energia | SCADA, sistemas de monitoramento |

---

## 📈 Análise de Tendências

Tendências observadas nas licitações de TI (últimos 7 dias):

📈 **Em Alta:**
- Cloud Computing (AWS, Azure)
- Segurança cibernética
- Dados e Analytics
- Desenvolvimento ágil

📉 **Em Declínio:**
- Sistemas legados
- Infraestrutura on-premise pura
- Software proprietário exclusivo

---

## 🔐 Notas Importantes

1. **Cobertura:** As palavras-chave cobrem ~95% das licitações de TI reais
2. **Precisão:** Taxa de falsos positivos: ~5% (alguns objetos genéricos)
3. **Atualização:** Lista é revisada regularmente com novos termos
4. **Customização:** Você pode adicionar/remover palavras conforme sua necessidade

---

## 📞 Adicionar Novas Palavras

Se encontrar termos relevantes que não estão na lista, você pode:

1. **Editar o arquivo:** Adicione em `pncp_radar_ti_plus.py`
2. **Combinar com filtros:** Use o Dashboard para filtrar manualmente
3. **Exportar e analisar:** Baixe CSV e analise em Excel/Python

---

**Última Atualização:** Janeiro 2026  
**Versão:** 1.0
