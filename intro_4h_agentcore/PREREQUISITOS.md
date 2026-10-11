# Prerrequisitos

Hay tres perfiles, con necesidades muy distintas:

| Perfil | Qué hace en el training | Qué necesita |
|---|---|---|
| **Asistente** | Mira, predice y pregunta. No programa. | [§1](#1-asistentes) |
| **Quien repite la demo** después, con este repositorio | Despliega el agente en su cuenta | [§2](#2-quien-repite-la-demo-con-este-repositorio) |
| **Formador** | Ejecuta la demo en directo | §2 + [§3](#3-formador-lista-de-comprobación) |

---

## 1. Asistentes

### Conocimientos

**Imprescindibles**
- Haber usado un asistente de IA conversacional (ChatGPT, Claude, Copilot…) y saber qué es un *prompt*.
- Conceptos básicos de nube, a nivel de «sé lo que es»: cuenta, región, servicio gestionado, permisos (usuario, rol, política).
- Saber qué es una API y reconocer un JSON.

**Recomendables** (aprovecharás más el training)
- Leer Python sencillo: funciones, `if`, diccionarios. Se enseña código corto y explicado; no hay que escribirlo.
- Haber oído hablar de *Infrastructure as Code* (Terraform o CloudFormation).
- Saber qué es un LLM por dentro a alto nivel (tokens, ventana de contexto). Se repasa en 5 minutos.

**No hace falta**
- Programar, tener cuenta de AWS ni instalar nada.

### Equipo y conexión
- Conexión estable y la herramienta de videoconferencia que indique la organización, con audio.
- Navegador reciente (Chrome, Edge o Firefox) para abrir las páginas interactivas de `teoria/`.
- **Recomendado:** dos pantallas, o una grande: en una la sesión, en otra las páginas interactivas.

### Preparación opcional (10 minutos)
Abre `teoria/index.html` (el mapa del agente), pulsa tres componentes y cambia entre «En tu máquina» y «En Internet».
Trae una pregunta: **¿qué te impide hoy poner un agente en producción?**

---

## 2. Quien repite la demo con este repositorio

### Cuenta de AWS
- Una cuenta **de pruebas** (*sandbox*), nunca la de producción.
- Región **`eu-west-1`** (Irlanda). AgentCore Runtime está en más regiones europeas (también en España), pero **Memory no está en todas**: comprueba la [tabla de regiones](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html) antes de cambiarla.
- **Modelos de Anthropic en Bedrock:** si es la primera vez que la cuenta usa Claude, Bedrock pide un formulario de caso de uso (una vez por cuenta). Comprueba que puedes invocarlo:
  ```
  aws bedrock list-inference-profiles --region eu-west-1 --query "inferenceProfileSummaries[?starts_with(inferenceProfileId, 'eu.anthropic')].inferenceProfileId" --output table
  ```
  Usa un perfil **`eu.`**: mantiene la inferencia dentro de la UE. Un `modelId` base, sin perfil, da `ValidationException`.
- **Cuotas:** las cuentas nuevas pueden tener cuotas de tokens por minuto bajas para Claude. Para una demo basta con las de por defecto; para varios alumnos a la vez, pide el aumento con días de antelación (*Service Quotas → Amazon Bedrock*).

### Permisos de quien despliega
Para `terraform apply` y `destroy`, tu usuario o rol necesita poder gestionar:
- `s3:*` sobre el bucket `tiendanova-intro-*`.
- `iam:CreateRole`, `iam:PutRolePolicy`, `iam:PassRole`, `iam:DeleteRole*`, `iam:Get*` sobre el rol `TiendaNovaIntro-runtime`.
- `bedrock-agentcore:*` del plano de control (Runtime y Memory) y `bedrock:ListInferenceProfiles`.

Para la demo:
- `bedrock:InvokeModel` (parte 1, en local).
- `bedrock-agentcore:InvokeAgentRuntime` y `bedrock-agentcore:ListMemoryRecords` (parte 2).

En una cuenta *sandbox*, un rol de administrador lo cubre todo.

### Herramientas en tu máquina

| Herramienta | Versión | Para qué |
|---|---|---|
| AWS CLI | v2 | Credenciales (`aws sso login` o `aws configure`) |
| Terraform | ≥ 1.9 | Desplegar `infra/` |
| Python | ≥ 3.10 (el agente desplegado usa 3.13) | Demo, scripts y tests |
| [uv](https://docs.astral.sh/uv/) | reciente | Empaquetar el agente para Linux arm64 |
| Git | cualquiera | Clonar el repositorio |

**No necesitas Docker:** el agente se despliega como zip de código.

### Coste
- **Runtime** cobra por uso activo (CPU mientras trabaja y memoria mientras la sesión vive); sin invocaciones no hay coste de cómputo.
- **Memory** cobra por eventos guardados y registros extraídos.
- **El modelo** (tokens) suele ser la parte mayor.

Una ejecución completa de la demo debería costar **del orden de céntimos a pocos dólares**. Es una estimación, no una medida:
mira la factura de tu ensayo y consulta la [página de precios](https://aws.amazon.com/bedrock/agentcore/pricing/).

**Al terminar, ejecuta siempre `terraform -chdir=infra destroy`.**

### Observabilidad (opcional)
Para ver las sesiones del agente en **CloudWatch → GenAI Observability**, activa *Transaction Search* una vez por cuenta:
*CloudWatch → Application Signals → Transaction Search → Enable*. Tiene coste por tramo ingerido; con un porcentaje de indexación bajo es mínimo.

---

## 3. Formador: lista de comprobación

### Una semana antes
- [ ] La cuenta cumple §2 y el perfil `eu.anthropic…` responde.
- [ ] **Ensayo completo**: `empaquetar.py` → `apply` → notebook entero → `destroy`. Apunta los tiempos reales de cada parte y el coste.
- [ ] **Graba en vídeo** las partes 1 y 2 del ensayo. Si algo falla en directo, pones el vídeo y sigues.
- [ ] Publica `teoria/` en una URL estática (GitHub Pages, S3 + CloudFront, Netlify…) y prueba que abre desde otro equipo.
- [ ] Comparte el repositorio con los asistentes.

### El día anterior
- [ ] `python scripts/empaquetar.py` y `terraform -chdir=infra apply`.
- [ ] Ejecuta el notebook completo una vez, para calentar y comprobar.
- [ ] **Vacía la memoria del ensayo.** Si no, Laura «ya prefiere WhatsApp» antes de decirlo y la predicción no sorprende a nadie:
  ```
  terraform -chdir=infra apply -replace=aws_bedrockagentcore_memory.nova
  ```

### 30 minutos antes
- [ ] `aws sts get-caller-identity` en el terminal del notebook (las credenciales SSO caducan).
- [ ] Notebook abierto con el kernel correcto y la celda de configuración ya ejecutada.
- [ ] Pestañas listas: `teoria/index.html`, consola de AgentCore (Runtime y Memory), CloudWatch GenAI Observability.
- [ ] Un **moderador** para el chat: con 26 personas online, alguien tiene que recoger las predicciones y las preguntas.
