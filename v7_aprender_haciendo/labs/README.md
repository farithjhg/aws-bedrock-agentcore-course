# Nova Assist — un curso de Amazon Bedrock AgentCore contado como una historia (edición 7, octubre 2026)

Notebooks del laboratorio del documento *Análisis de la Arquitectura Empresarial de Amazon Bedrock AgentCore* (edición 7, sección 15). Si impartes el curso, la agenda, la logística, el coste y las respuestas esperadas están en [`../GUIA_FORMADOR.md`](../GUIA_FORMADOR.md).

**Empieza por la [presentación](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/presentacion_nova_assist.html)**: cuenta la historia, y desde cada capítulo abre su notebook en Colab y su página de teoría.

TiendaNova, un e-commerce ficticio, necesita un asistente de postventa. Cada capítulo empieza con una **escena** que falla con lo construido hasta ahí y termina con un **descubrimiento**, que es la necesidad del capítulo siguiente. Se aprende haciendo: **✋ predice → ▶️ ejecuta → 🔍 comprueba → 🧭 teoría → ↩️ vuelve**. Cuando un resultado depende del modelo, una celda lo comprueba con código: un modelo no falla siempre igual, y lo que importa es lo que demuestra la comprobación.

## Puesta en marcha

Requisitos comunes: acceso a **tu propia cuenta *sandbox*** (una por participante) y cuotas de Bedrock suficientes para el modelo (capítulo 0, B5b).

### Opción A · Google Colab (sin instalar nada)

1. Abre el capítulo 0 en Colab: [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/00_configuracion_cuenta_aws.ipynb) (o desde su escena en la presentación).
2. En el panel **Secretos** (icono 🔑) crea `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` y, si tus credenciales son temporales (portal de IAM Identity Center → *Access keys*), `AWS_SESSION_TOKEN`. Opcional: `AWS_REGION` (por defecto `eu-west-1`). Activa el acceso del notebook a cada secreto.
3. Ejecuta la **celda ☁️** (la primera de código): descarga el curso, monta tu Google Drive, instala las dependencias, Node.js y la AgentCore CLI 0.31.1 y comprueba la cuenta. Tarda 2–3 minutos.
4. Sigue el notebook. Tu estado (`lab_state.json`, el proyecto `NovaAssist`, `datos/`, las partidas) se guarda solo en `MyDrive/NovaAssist_curso`; `guardar_en_drive()` lo fuerza.
5. Al terminar, el enlace del final abre el capítulo siguiente. **Cada notebook abre una máquina nueva**: su celda ☁️ recupera tu estado de Drive.

- Si las credenciales caducan (`ExpiredToken`), copia las nuevas en los Secretos y repite la celda ☁️. Lo mismo si Colab desconecta la sesión: no se pierde nada.
- Si Colab pide reiniciar la sesión tras instalar, reinicia y repite la celda: la segunda vez no reinstala.
- En Colab no hay Agent Inspector (`agentcore dev`, opcional en el capítulo 3). Si un despliegue pidiera datos de forma interactiva, usa la Terminal de Colab desde `/content/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/NovaAssist`.

### Opción B · En tu equipo

Requisitos: Python 3.10 o superior, Node.js 20 o superior y AWS CLI v2.

```bash
cd labs
# macOS / Linux
python3 -m venv .venv && source .venv/bin/activate
# Windows (PowerShell)
py -m venv .venv ; .venv\Scripts\Activate.ps1

pip install -r requirements.txt
npm install -g @aws/agentcore@0.31.1   # la versión con la que se probó el curso
jupyter lab
```

- Empieza por `00_configuracion_cuenta_aws.ipynb` y **ejecuta siempre los notebooks desde esta carpeta**. La celda ☁️ no hace nada fuera de Colab.
- **Windows:** si PowerShell no deja activar el entorno, `Set-ExecutionPolicy -Scope Process RemoteSigned`. La CLI se instala como `agentcore.cmd`; los notebooks la llaman con `cli()` y `cli_args()`, que la encuentran solos y funcionan igual en los tres sistemas. El servidor MCP local del capítulo 7 se lanza como proceso aparte por la misma razón.

### En los dos casos

- **No actualices la CLI durante el curso.** Si usas otra versión, ensaya antes con ella.
- **Navegación.** La presentación, cada notebook y cada página de teoría se enlazan entre sí: arriba de cada notebook tienes su escena, su teoría y los capítulos vecinos; en cada página de teoría, *Volver al capítulo* y *Ver la escena*.
- **Páginas de teoría** (`teoria/`): se publican con GitHub Pages en [https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/index.html), y es ahí adonde llevan los enlaces de los notebooks. Abiertas desde JupyterLab muestran un aviso hasta que pulsas **Trust HTML**.

## Capítulos

| Notebook (abre en Colab) | Capítulo | La necesidad | Teoría (🧭) |
|---|---|---|---|
| [`00_configuracion_cuenta_aws`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/00_configuracion_cuenta_aws.ipynb) | 0 · El terreno | Cuenta, presupuesto, cuotas, observabilidad y los datos de TiendaNova en Iceberg | [`teoria/index.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/index.html) (el mapa) |
| [`01_agente_simple`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/01_agente_simple.ipynb) | 1 · El agente que sabe… lo que no es | Que no conteste con la regla general en lugar de la de TiendaNova | [`teoria/cap01-modelo-e-instrucciones.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap01-modelo-e-instrucciones.html) |
| [`02_herramientas`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/02_herramientas.ipynb) | 2 · El agente que no ve tus datos | Acceso a los pedidos | [`teoria/cap02-herramientas.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap02-herramientas.html) |
| [`03_runtime`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/03_runtime.ipynb) | 3 · Del portátil a la nube | Disponible y aislado para miles de clientes | [`teoria/cap03-runtime.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap03-runtime.html) |
| [`04_memoria_corto_plazo`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/04_memoria_corto_plazo.ipynb) | 4 · El agente que olvida tu nombre | Que la conversación sobreviva a la microVM | [`teoria/cap04-memoria-corto-plazo.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap04-memoria-corto-plazo.html) |
| [`05_memoria_largo_plazo`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/05_memoria_largo_plazo.ipynb) | 5 · El agente que no te reconoce mañana | Recordar entre sesiones, y poder olvidar (RGPD) | [`teoria/cap05-memoria-largo-plazo.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap05-memoria-largo-plazo.html) |
| [`06_contexto_y_coste`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/06_contexto_y_coste.ipynb) | 6 · La cuenta del taxímetro | Controlar qué entra en el contexto | [`teoria/cap06-contexto-y-coste.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap06-contexto-y-coste.html) |
| [`07_gateway`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/07_gateway.ipynb) | 7 · Herramientas compartidas y gobernadas | Herramientas para varios agentes, con control | [`teoria/cap07-mcp-gateway.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap07-mcp-gateway.html) |
| [`08_rag_iceberg_s3vectors`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/08_rag_iceberg_s3vectors.ipynb) | 8 · La biblioteca de la empresa | Responder con documentos y fuentes | [`teoria/cap08-rag.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap08-rag.html) |
| [`09_identidad`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/09_identidad.ipynb) | 9 · Saber quién habla | Identidad verificada por la plataforma | [`teoria/cap09-identidad.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap09-identidad.html) |
| [`10_policy_guardrails`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/10_policy_guardrails.ipynb) | 10 · Reglas que el modelo no puede saltarse | Límites deterministas y detección de ataques | [`teoria/cap10-policy-guardrails.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap10-policy-guardrails.html) |
| [`11_code_interpreter`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/11_code_interpreter.ipynb) | 11 · Cuentas exactas | Cálculos verificables | [`teoria/cap11-code-interpreter.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap11-code-interpreter.html) |
| [`12_observabilidad_evaluacion`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/12_observabilidad_evaluacion.ipynb) | 12 · ¿Lo hace bien? | Medir calidad y poner techo al coste | [`teoria/cap12-observabilidad-evaluacion.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap12-observabilidad-evaluacion.html) |
| [`13_ab_testing`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/13_ab_testing.ipynb) | 13 · Mejorar sin romper | Cambiar el comportamiento con datos (A/B real) | [`teoria/cap13-ab-testing.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap13-ab-testing.html) |
| [`14_equipo_investigacion`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/14_equipo_investigacion.ipynb) | 14 · Del agente al equipo | Investigar, analizar y redactar | [`teoria/cap14-multiagente.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap14-multiagente.html) |
| [`15_produccion`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/15_produccion.ipynb) | 15 · Producción | Versiones, *endpoints*, puerta de calidad y *rollback* | [`teoria/cap15-operacion.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/labs/teoria/cap15-operacion.html) |
| [`16_tu_escena`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/16_tu_escena.ipynb) | 16 · Tu escena (sin guion) | Decidir solo qué piezas hacen falta | El mapa, como herramienta de diseño |
| [`17_limpieza`](https://colab.research.google.com/github/farithjhg/aws-bedrock-agentcore-course/blob/main/v7_aprender_haciendo/labs/17_limpieza.ipynb) | 17 · Apagarlo todo | Que nada del laboratorio siga facturando | — |

El componente de cada capítulo, si funciona en local y por qué AWS al salir a Internet: sección 15.2 del documento.

## Recursos que atraviesan el curso

- **📒 Cuaderno de deudas** (`cuaderno()`): problemas que aparecen antes de poder resolverlos (D0–D8). Algunas se pagan solo si la comprobación del capítulo pasa; si no, quedan parciales, y eso también se cuenta.
- **🚕 Taxímetro** (`taximetro()`, `taximetro_historico()`, `comparar_conversaciones()`): *tokens* a precio completo, en caché y de salida, y coste estimado por conversación y por capítulo. Fija el precio del modelo en el capítulo 0 (B6).
- **💾 Puntos de guardado:** cada capítulo termina con `guardar_partida(N)` y empieza con `requisitos(N)`. Si llegas tarde o algo se rompe, descomenta `ponerse_al_dia(N)`. Las partidas no se pueden copiar entre cuentas.

## Organización

```text
labs/
├── README.md, requirements.txt, .gitignore
├── lab_utils.py            # estado, CLI, invocación, comprobaciones, taxímetro, cuaderno, Iceberg/Athena, Gateway, Memory, limpieza
├── colab_nova.py           # celda ☁️: prepara Colab (Drive, dependencias, CLI, credenciales de los Secretos)
├── dataset_tiendanova.py   # dataset sintético reproducible (fechas relativas al día de carga)
├── rag_nova.py             # troceado, embeddings (Titan V2), indexado y consultas a S3 Vectors
├── 00_…17_*.ipynb
├── teoria/                 # páginas de teoría interactivas y el mapa del agente (index.html)
├── lab_state.json          # estado compartido (se crea en el capítulo 0; NO versionar: contiene secretos de laboratorio)
├── partidas/               # puntos de guardado (NO versionar)
├── mcp_local/              # servidor y cliente MCP locales (capítulo 7)
├── lambda/                 # Lambdas nova-pedidos (Athena/Iceberg) y nova-politicas (S3 Vectors)
├── datos/                  # copia local del dataset
└── NovaAssist/             # proyecto de la AgentCore CLI (capítulo 3); NovaAgent y NovaWeb (capítulo 13)
```

**Datos.** El capítulo 0 carga en **S3 Tables (Apache Iceberg)** las tablas `clientes`, `productos`, `pedidos`, `lineas_pedido`, `envios_eventos`, `devoluciones`, `documentos` y `eval_casos`. El capítulo 8 crea `chunks`, el 12 `eval_retrieval` y el 14 `informes`. El índice vectorial vive en **S3 Vectors** desde el capítulo 8.

## Versiones probadas

| Paquete | Versión |
|---|---|
| AgentCore CLI (`@aws/agentcore`) | 0.31.1 |
| `strands-agents` | 1.55.1 |
| `bedrock-agentcore[strands-agents]` | 1.22.0 |
| `strands-agents-tools[agent_core_code_interpreter]` | 0.8.9 |
| `mcp` | 1.30.0 |
| `pyiceberg[pyarrow]` | 0.12.0 |

> ⚠️ **`strands-agents` 1.57 o superior rompe la integración de Memory de `bedrock-agentcore` 1.22** (`ImportError: BidiAfterInvocationEvent`). Por eso las versiones van fijadas en `requirements.txt` y en el agente desplegado (`fijar_dependencia(...)` en los capítulos 3, 4, 7 y 11).

## Solución de problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ImportError: BidiAfterInvocationEvent` | `strands-agents` demasiado nuevo | Versiones de la tabla anterior |
| `ThrottlingException` en los capítulos 6, 12–15 | Cuotas de Bedrock bajas en la cuenta | Capítulo 0, B5b; pide el aumento en Service Quotas |
| `ValidationException` sobre *on-demand throughput* | Se usa el `modelId` base | ID del inference profile (`eu.…`) |
| `AccessDenied` en `InvokeModel` | Faltan permisos sobre el perfil o sus modelos de destino | Doc §2.4; revisa las SCP |
| `agentcore` no responde | Lo oculta el *starter toolkit* de pip, o el `PATH` de npm | `pip uninstall bedrock-agentcore-starter-toolkit`; terminal nueva |
| Una opción de la CLI no existe | Otra versión de la CLI | `agentcore --version` (0.31.1) y `agentcore <comando> --help` |
| Athena no ve las tablas | Falta el catálogo `s3tablescatalog` | Capítulo 0, paso A7 (o *Enable integration* en la consola de S3) |
| `tools/list` devuelve 404 o 405 | Gateway creado como HTTP | Capítulo 7: `--protocol-type MCP` |
| `UnknownServiceError: s3vectors` en Lambda | boto3 antiguo en el *runtime* de Lambda | Empaqueta un boto3 reciente con la Lambda (capítulo 8, §5) |
| La memoria a largo plazo no devuelve nada | Extracción asíncrona, o *namespace* distinto | `esperar_registros()`; compara con `namespaces_memoria()` |
| Tras activar Policy se deniega todo | Denegación por defecto | Permite también las herramientas nuevas (capítulos 10 y 14) |
| Error al invocar el Runtime tras el capítulo 9 | Ya no se aceptan invocaciones sin token de cliente | `invocar(..., token=token_cliente("C-001"))` |
| La evaluación no encuentra la sesión | Trazas aún no indexadas, o sin Transaction Search | Espera de 5 a 10 minutos; capítulo 0, paso A4 |
| Sin resultados del A/B | El análisis tarda unos 15 minutos | Repite la celda de resultados (capítulo 13) |
| Una página de teoría sale en blanco o con un aviso | JupyterLab no ejecuta sus *scripts* | Ábrela desde el enlace del notebook (GitHub Pages), o *Trust HTML* |
| `ExpiredToken` en Colab | Credenciales temporales caducadas | Actualiza los Secretos y repite la celda ☁️ |
| En Colab falta lo del capítulo anterior | No se ejecutó la celda ☁️, o Drive no estaba montado | Ejecuta la celda ☁️; `requisitos(N)` dice qué falta |

## Coste y seguridad

- Cada participante, en su propia cuenta *sandbox*, con el presupuesto del capítulo 0. El coste orientativo por participante está en la guía del formador (sección 4).
- **Al terminar, ejecuta el capítulo 17**: borra también lo que no gestiona la CLI (Lambdas, Cognito, guardrail, *rate limits*, A/B, datos y logs).
- `lab_state.json`, `partidas/` y `NovaAssist/agentcore/.env.local` contienen secretos de laboratorio (el *secret* M2M, la contraseña de los usuarios de prueba): están en `.gitignore`. No los compartas.
