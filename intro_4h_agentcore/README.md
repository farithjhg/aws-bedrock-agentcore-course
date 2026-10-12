# AgentCore en 4 horas · Nova Assist

Introducción a **Amazon Bedrock AgentCore** con un ejemplo real, desplegado con **Terraform**.
Un agente de atención al cliente (Nova Assist, de la tienda ficticia TiendaNova) que nace en tu portátil
y sale a Internet con **AgentCore Runtime** y **AgentCore Memory**.

- **Para seguir el training:** la [presentación](https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/presentacion_intro.html) y el [mapa del agente](https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/teoria/index.html), publicados con GitHub Pages.
- **Para impartirlo:** [`AGENDA.md`](AGENDA.md) (agenda y guion) y [`PREREQUISITOS.md`](PREREQUISITOS.md).
- **Para repetirlo en tu cuenta:** [en Google Colab, sin instalar nada](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/demo/demo_intro.ipynb) (abajo, opción A), o en tu equipo con Terraform (opción B).
- **Para construirlo todo tú:** el [curso completo de 3,5 días](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/), aprender haciendo, con las quince piezas.

[![Abrir la demo en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/demo/demo_intro.ipynb)

## Qué hay en el repositorio

```
presentacion_intro.html  La presentación del training: la placa del agente animada, escena a escena (GitHub Pages)
agent/                 El agente (Strands Agents + AgentCore): el mismo código en local y en Runtime
  main.py              Punto de entrada de Runtime
  herramientas.py      Herramientas con las reglas de negocio en código
  memoria.py           AgentCore Memory: corto plazo (sesión) y largo plazo (preferencias)
  datos.py             Datos de ejemplo (fechas relativas a hoy)
infra/                 Terraform: S3 (código), IAM (rol mínimo), Memory, Runtime
scripts/
  empaquetar.py        Empaqueta el agente como zip para Linux arm64 (sin Docker)
  despliegue.py        Desplegar y apagar desde Python: modelos(), desplegar(), apagar() (la Parte 0 del notebook)
  nova.py              Habla con el agente desplegado (línea de comandos y notebook)
  colab_intro.py       La celda ☁️: prepara Google Colab (Drive, uv, Terraform, credenciales de los Secretos)
demo/demo_intro.ipynb  La demo del training: Parte 0 (desplegar) y tres partes (nace, sale a Internet, se opera)
teoria/                Páginas interactivas: el mapa del agente y una por componente (GitHub Pages)
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

### Opción A · Google Colab (sin instalar nada)

1. Abre [la demo en Colab](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/demo/demo_intro.ipynb).
2. En el panel **Secretos** (icono 🔑) crea `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` y, si tus credenciales son temporales (portal de IAM Identity Center → *Access keys*), `AWS_SESSION_TOKEN`. Opcional: `AWS_REGION` (por defecto `eu-west-1`). Activa el acceso del notebook a cada secreto.
3. Ejecuta la **celda ☁️**: descarga el repositorio, monta tu Google Drive, instala `uv` y Terraform y comprueba la cuenta (2–3 minutos).
4. **Parte 0:** `modelos()` lista los perfiles `eu.anthropic…`; `desplegar("eu.anthropic…")` empaqueta, hace `terraform init` y `apply` (3–5 minutos).
5. Sigue el notebook. Al terminar, la última celda ejecuta `terraform destroy`.

El estado de Terraform, `terraform.tfvars` y el zip se guardan en `MyDrive/NovaAssist_intro`: si Colab abre una máquina nueva, la celda ☁️ los recupera y `apagar()` sigue sabiendo qué borrar. Los proveedores de Terraform (cientos de MB) van a la máquina de Colab, no a Drive.

### Opción B · En tu equipo

Los comandos valen en PowerShell y en bash, salvo donde se indica. Las celdas de la Parte 0 del notebook hacen lo mismo que los pasos 1 a 3.

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
(o la última celda del notebook, que pide confirmación).

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
Validado también: `despliegue.py` y la celda ☁️ en una simulación de Colab (Drive, Secretos y Terraform simulados), la presentación y las páginas de teoría en el navegador (escritorio y móvil).
**Pendiente del primer ensayo en una cuenta real:** `apply`, la demo completa (en local y en Colab) y la medida del coste.

Las páginas de `teoria/` son las del [curso completo de 3,5 días](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/) (edición 7), con los enlaces propios del training: volver al mapa, abrir la demo y, en cada una, «constrúyelo tú» hacia el capítulo del curso en Colab. Se regeneran con el mismo generador que las del curso.
