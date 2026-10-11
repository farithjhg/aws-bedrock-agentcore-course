# AgentCore en 4 horas · Nova Assist

Introducción a **Amazon Bedrock AgentCore** con un ejemplo real, desplegado con **Terraform**.
Un agente de atención al cliente (Nova Assist, de la tienda ficticia TiendaNova) que nace en tu portátil
y sale a Internet con **AgentCore Runtime** y **AgentCore Memory**.

- **Para el training:** [`AGENDA.md`](AGENDA.md) (agenda y guion) y [`PREREQUISITOS.md`](PREREQUISITOS.md).
- **Para repetirlo en tu cuenta:** sigue los pasos de abajo.

## Qué hay en el repositorio

```
agent/                 El agente (Strands Agents + AgentCore): el mismo código en local y en Runtime
  main.py              Punto de entrada de Runtime
  herramientas.py      Herramientas con las reglas de negocio en código
  memoria.py           AgentCore Memory: corto plazo (sesión) y largo plazo (preferencias)
  datos.py             Datos de ejemplo (fechas relativas a hoy)
infra/                 Terraform: S3 (código), IAM (rol mínimo), Memory, Runtime
scripts/
  empaquetar.py        Empaqueta el agente como zip para Linux arm64 (sin Docker)
  nova.py              Habla con el agente desplegado (línea de comandos y notebook)
demo/demo_intro.ipynb  La demo del training, en tres partes
teoria/                Páginas interactivas: el mapa del agente y una por componente
tests/                 Tests de las reglas de negocio (sin AWS)
```

## Arquitectura

```
Tu portátil ──InvokeAgentRuntime──▶ AgentCore Runtime (microVM por sesión)
                                      │  agent/main.py · Strands Agent
                                      ├──▶ Amazon Bedrock (perfil eu.anthropic…)
                                      └──▶ AgentCore Memory
                                             ├─ eventos de la sesión (corto plazo)
                                             └─ /users/{actorId}/preferences (largo plazo)
```

## Desplegar y probar

Requisitos: [`PREREQUISITOS.md` §2](PREREQUISITOS.md#2-quien-repite-la-demo-con-este-repositorio).
Los comandos valen en PowerShell y en bash, salvo donde se indica.

**1. Elige el modelo**
```
aws bedrock list-inference-profiles --region eu-west-1 --query "inferenceProfileSummaries[?starts_with(inferenceProfileId, 'eu.anthropic')].inferenceProfileId" --output table
```
Copia `infra/terraform.tfvars.example` como `infra/terraform.tfvars` y pon el perfil elegido en `model_id`.

**2. Entorno de Python y tests**
```
uv venv .venv
.venv\Scripts\activate          # bash: source .venv/bin/activate
uv pip install -r requirements.txt
python -m pytest tests
```

**3. Empaqueta el agente y despliega**
```
python scripts/empaquetar.py
terraform -chdir=infra init
terraform -chdir=infra apply
```

**4. Habla con el agente**
```
python scripts/nova.py "¿Dónde está mi pedido TN-1003?" --cliente C-001
jupyter lab demo/demo_intro.ipynb
```
Si cambias el código de `agent/`, repite `empaquetar.py` y `apply`: cada zip nuevo crea una versión nueva del Runtime.

**5. Apaga todo**
```
terraform -chdir=infra destroy
```

## Decisiones de diseño
- **Un `Agent` nuevo por invocación.** Así nunca se comparte estado entre clientes. Runtime sí mantiene la misma microVM
  para la misma sesión; la continuidad de la conversación la pone Memory.
- **Las reglas viven en las herramientas.** El plazo, el coste de devolución y quién ve qué pedido son código y tienen tests.
- **El `cliente_id` va en el payload** para simplificar la demo. En producción sale del token del usuario
  (AgentCore Identity con un autorizador JWT): el cliente no debe poder elegir quién es.
- **Un solo namespace de Memory**, definido en Terraform y pasado al agente por variable de entorno.
- **Perfil `eu.`** para que la inferencia no salga de la UE.

## Estado
Validado: tests de las reglas de negocio, `terraform validate`, empaquetado del zip para arm64 y las APIs usadas contra las versiones fijadas
(`strands-agents 1.55.1`, `bedrock-agentcore 1.22.0`, proveedor AWS de Terraform `6.68`).
**Pendiente del primer ensayo en una cuenta real:** `apply`, la demo completa y la medida del coste.

Las páginas de `teoria/` vienen del curso completo de 3 días; sus referencias a «capítulos» son de ese curso.
