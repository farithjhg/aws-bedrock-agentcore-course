# Nova Assist — un curso de Amazon Bedrock AgentCore contado como una historia (octubre 2026)

Notebooks del laboratorio del documento *Análisis de la Arquitectura Empresarial de Amazon Bedrock AgentCore* (edición práctica, sección 15).

TiendaNova, un e-commerce ficticio, necesita un asistente de postventa. Cada capítulo empieza con una **escena**, un mensaje de un cliente que falla con lo construido hasta ahí, y termina con un **descubrimiento**, que es la necesidad del capítulo siguiente. En paralelo corre el **hilo de producción**: lo que se rompe cuando un agente sale del portátil y el componente de AWS que lo resuelve.

## Puesta en marcha

```bash
cd labs
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install -g @aws/agentcore      # AgentCore CLI (Node.js 20+)
jupyter lab
```

Empieza por `00_configuracion_cuenta_aws.ipynb`. **Ejecuta siempre los notebooks desde esta carpeta.** Si impartes el curso, lee antes `../GUIA_FORMADOR.md`.

## Capítulos

| Notebook | Capítulo | La necesidad | En el ordenador sería… |
|---|---|---|---|
| `00_configuracion_cuenta_aws` | 0 · El terreno | Cuenta, presupuesto, observabilidad y la plataforma de datos de TiendaNova (Iceberg) | — |
| `01_agente_simple` | 1 · El agente que inventa | Que no invente | La ROM |
| `02_herramientas` | 2 · El agente que no ve tus datos | Acceso a los pedidos | Periféricos de E/S |
| `03_runtime` | 3 · Del portátil a la nube | Disponible y aislado para miles de clientes | Encender el ordenador para todos |
| `04_memoria_corto_plazo` | 4 · El agente que olvida tu nombre | Recordar la conversación | La RAM |
| `05_memoria_largo_plazo` | 5 · El agente que no te reconoce mañana | Recordar entre sesiones | El disco duro |
| `06_contexto_y_coste` | 6 · La cuenta del taxímetro | Controlar qué entra en el contexto | Gestión de memoria del SO |
| `07_gateway` | 7 · Herramientas compartidas y gobernadas | Herramientas para varios agentes, con control | El bus y los controladores |
| `08_rag_iceberg_s3vectors` | 8 · La biblioteca de la empresa | Responder con documentos y fuentes | La biblioteca con su índice |
| `09_identidad` | 9 · Saber quién habla | Identidad verificada | Las cuentas de usuario |
| `10_policy_guardrails` | 10 · Reglas que el modelo no puede saltarse | Límites deterministas | Permisos y antivirus |
| `11_code_interpreter` | 11 · Cuentas exactas | Cálculos sin errores | El coprocesador matemático |
| `12_observabilidad_evaluacion` | 12 · ¿Lo hace bien? | Medir calidad y coste | Visor de eventos y exámenes |
| `13_ab_testing` | 13 · Mejorar sin romper | Cambiar con datos | Probar una actualización en pocos equipos |
| `14_equipo_investigacion` | 14 · Del agente al equipo | Investigar, analizar y redactar | Una red de equipos especializados |
| `15_produccion_y_limpieza` | 15 · Producción y cierre | Operar y apagar bien | El mantenimiento |
| `16_tu_escena` | 16 · Tu escena (sin guion) | Decidir solo qué piezas hacen falta | — |

## La teoría manda; AWS entra al salir a Internet

La columna vertebral son los **componentes de un agente**. Cada capítulo enseña uno; si se puede, lo prueba en local; y AWS entra cuando el agente tiene que estar en Internet y lo local deja de funcionar o no aplica.

- **Acto I · Nace un agente (en tu máquina):** capítulos 1, 2
- **Acto II · Sale a Internet:** capítulos 3, 4, 5, 6, 7, 8, 9, 10, 11
- **Acto III · Crece y se opera:** capítulos 12, 13, 14, 15
- **Epílogo · Tu escena:** capítulo 16

| Cap. | Componente agéntico | ¿En local? | Por qué AWS al salir a Internet |
|---|---|---|---|
| 1 | Modelo e instrucciones: el razonamiento | ✅ | Bedrock: IAM sin claves, perfil `eu.`, cuotas y reintentos |
| 2 | Herramientas y bucle del agente: la acción | ✅ | Todavía ninguno |
| 3 | Entorno de ejecución: el agente como servicio | ☁️ | Runtime: microVM por sesión, escala y disponibilidad |
| 4 | Memoria de trabajo y a corto plazo | ✅ | Memory: estado compartido entre réplicas |
| 5 | Memoria a largo plazo | ⚠️ | Memory: extracción, namespaces y borrado gestionados |
| 6 | Contexto: qué ve el modelo en cada llamada | ✅ | Bedrock: caché del prefijo; el resto es diseño |
| 7 | Interoperabilidad de herramientas (MCP) | ✅ | Gateway: publicar MCP con autenticación, límites y trazas |
| 8 | Conocimiento: recuperación aumentada (RAG) | ✅ | S3 Vectors + Iceberg: índice compartido y con linaje |
| 9 | Identidad y delegación | ☁️ | Identity: tokens validados, Token Vault y OBO |
| 10 | Guardarraíles y gobernanza | ⚠️ | Policy y Guardrails en la frontera del Gateway |
| 11 | Ejecución de código (código como acción) | ⛔ | Code Interpreter: *sandbox* en microVM |
| 12 | Observabilidad y evaluación | ✅ | Observability y Evaluations sobre tráfico real |
| 13 | Mejora continua y experimentación | ☁️ | Configuration bundles y A/B en el Gateway |
| 14 | Orquestación multi-agente | ✅ | Web Search, datos en Iceberg y ejecución asíncrona en Runtime |
| 15 | Ciclo de vida y operación | ☁️ | CDK, entornos, versiones y limpieza |

> ✅ funciona en local · ⚠️ incompleto o parcial · ⛔ peligroso · ☁️ solo existe al salir a Internet.

## Recursos que atraviesan el curso

- **📒 Cuaderno de deudas** (`cuaderno()`): problemas que aparecen antes de poder resolverlos. Se abren cuando se descubren y se pagan más adelante: acceso a pedidos ajenos, reembolsos sin límite, cálculos del modelo, suplantación, memoria envenenada, coste, falta de login y documentos envenenados.
- **🚕 Taxímetro** (`taximetro()`, `taximetro_historico()`): *tokens* y coste estimado por conversación y por capítulo. Fija el precio del modelo en el capítulo 0 (paso B6).
- **💾 Puntos de guardado**: cada capítulo termina con `guardar_partida(N)` y empieza con `requisitos(N)`. Si llegas tarde o algo se rompe, `ponerse_al_dia(N)` carga la partida anterior o escribe el código de referencia y te dice qué recursos faltan. No se pueden copiar entre cuentas de AWS.
- **Experimentos de rotura**: primero se rompe la versión local y después se arregla. Ejemplos: un agente global que filtra datos entre usuarios, dos réplicas con memoria en el proceso, `exec()` de código generado y un documento envenenado.

## Organización

```text
labs/
├── README.md, requirements.txt, .gitignore
├── lab_utils.py            # estado, settings, invocación, taxímetro, cuaderno, Iceberg/Athena, Gateway, tokens
├── dataset_tiendanova.py   # dataset sintético reproducible (fechas relativas al día de carga)
├── rag_nova.py             # troceado, embeddings (Titan V2), indexado y consultas directas a S3 Vectors
├── lab_state.json          # estado compartido entre notebooks (se crea en el capítulo 0; NO versionar)
├── partidas/               # puntos de guardado por capítulo (NO versionar)
├── 00_…16_*.ipynb
├── mcp_local/              # servidor MCP local por stdio (capítulo 7, sección 0)
├── lambda/                 # Lambdas nova-pedidos (Athena/Iceberg) y nova-politicas (S3 Vectors)
├── datos/                  # copia local del dataset
└── NovaAssist/             # proyecto de la AgentCore CLI (se crea en el capítulo 3)
```

**Datos.** El capítulo 0 (Parte C) carga en **S3 Tables (Apache Iceberg)** las tablas `clientes`, `productos`, `pedidos`, `lineas_pedido`, `envios_eventos`, `devoluciones`, `documentos` y `eval_casos`. El capítulo 8 crea `chunks`, el 12 `eval_retrieval` y el 14 `informes`. El índice vectorial vive en **S3 Vectors** y se crea en el capítulo 8, cuando la historia lo necesita.

## Versiones probadas

| Paquete | Versión |
|---|---|
| `strands-agents` | 1.55.1 |
| `bedrock-agentcore[strands-agents]` | 1.22.0 |
| `strands-agents-tools[agent_core_code_interpreter]` | 0.8.9 |
| `mcp` | 1.30.0 |
| `pyiceberg[pyarrow]` | 0.12.0 |

> ⚠️ **`strands-agents` 1.57 o superior rompe la integración de Memory de `bedrock-agentcore` 1.22** (`ImportError: BidiAfterInvocationEvent`). Por eso las versiones van fijadas, tanto en `requirements.txt` como en el agente desplegado (`fijar_dependencia(VERSIONES[...])` en los capítulos 3, 4, 7, 11 y 13). Antes de subir versiones, prueba la importación de `AgentCoreMemorySessionManager`.

## Puntos que conviene verificar en el primer ensayo

- Cómo pide `agentcore deploy` las credenciales OAuth del Gateway con `CUSTOM_JWT` (capítulo 7).
- El campo de `agentcore.json` para el autorizador JWT del Runtime y la *allowlist* de la cabecera `Authorization` (capítulo 9).
- Las *flags* de `add gateway-target` para conectores (Web Search, capítulo 14) y de `add config-bundle` y `run ab-test` (capítulo 13). Los notebooks muestran la ayuda antes de cada paso.
- La disponibilidad regional de Web Search, Evaluations y de la integración de S3 Tables con Athena por IAM.

## Solución de problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ImportError: BidiAfterInvocationEvent` | `strands-agents` demasiado nuevo | Versiones de la tabla anterior |
| `ValidationException` sobre *on-demand throughput* | Se usa el `modelId` base | ID del inference profile (`eu.…`) |
| `AccessDenied` en `InvokeModel` | Faltan permisos sobre el perfil o sus modelos de destino | Doc §2.4; revisa las SCP |
| `agentcore` no responde | Lo oculta el *starter toolkit* de pip | `pip uninstall bedrock-agentcore-starter-toolkit` |
| Una *flag* de la CLI no existe | Cambio de versión | `agentcore <comando> --help`, `agentcore update` |
| Athena no ve las tablas | Falta el catálogo `s3tablescatalog` | Capítulo 0, paso A8 (o *Enable integration* en la consola de S3) |
| `UnknownServiceError: s3vectors` en Lambda | boto3 antiguo en el *runtime* | Empaqueta un boto3 reciente con la Lambda |
| La memoria a largo plazo no devuelve nada | Extracción asíncrona, o namespace distinto o sin `/` final | Espera; compara con `get_memory` |
| El agente no ve herramientas del Gateway | URL sin `/mcp` o token inválido | `mcp_tools_list(token=token_m2m())` |
| Tras activar Policy se deniega todo | Denegación por defecto | Permite también las herramientas nuevas (capítulos 10 y 14) |
| 401 al invocar el Runtime tras el capítulo 9 | Ya no se acepta SigV4 | `invocar(..., token=token_cliente("C-001"))` |
| La evaluación no encuentra la sesión | Sin Transaction Search o trazas aún no disponibles | Capítulo 0, paso A4; espera unos minutos |

## Coste y seguridad

- Los capítulos consumen recursos de pago. Usa una cuenta de *sandbox* (una por participante, idealmente), configura el presupuesto del capítulo 0 y ejecuta el 15 al terminar.
- `lab_state.json` contiene el *client secret* M2M y la contraseña de los usuarios de prueba: está en `.gitignore`. No lo compartas.
