# Agenda y guion · AgentCore en 4 horas (online)

**Formato:** demo guiada. El formador comparte pantalla con la [presentación](https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/presentacion_intro.html) y ejecuta `demo/demo_intro.ipynb` (en Colab o en local); los asistentes predicen en el chat.
**La presentación** sigue esta agenda escena a escena (apertura, mapa, demo 1, demo 2, catálogo, coste y cierre), con la placa del agente animada; desde cada escena se abre la demo en Colab (▶, tecla C) y la página de teoría (🧭, tecla T). Teclas: → y ←, **N** notas del presentador (este guion, resumido), **O** índice, **F** pantalla completa. Cada bloque tiene su enlace: `…/presentacion_intro.html#demo1`, `#sesiones`, `#catalogo-herramientas`, `#coste`…
**Hilo conductor:** TiendaNova, una tienda online, quiere un agente de atención al cliente (Nova Assist). Laura es una clienta.
**Principio:** la teoría manda; AWS entra cuando el agente sale a Internet.

| Hora | Bloque | Material |
|---|---|---|
| 0:00–0:15 | Apertura | — |
| 0:15–0:40 | El mapa del agente | [`teoria/index.html`](https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/teoria/index.html) · escena `#mapa` |
| 0:40–1:25 | 💻 Demo 1 · Nace en tu máquina | Notebook, parte 1 · `cap01`, `cap02` · escenas `#demo1`, `#reglas` |
| 1:25–1:35 | *Descanso* | |
| 1:35–2:20 | 💻 Demo 2 · Sale a Internet | Notebook, parte 2 · `infra/main.tf` · `cap03`, `cap04`, `cap05` · escenas `#terraform`, `#sesiones`, `#memoria` |
| 2:20–3:05 | 🗺️ El resto del catálogo | `cap07`–`cap15` · escenas `#catalogo-herramientas`, `#catalogo-control`, `#catalogo-operacion`, `#martes` |
| 3:05–3:15 | *Descanso* | |
| 3:15–3:40 | Coste, operación y decisión | Notebook, parte 3 · `cap06` · consola · escenas `#coste`, `#decision` |
| 3:40–4:00 | Preguntas y siguiente paso | `README.md` · escena `#siguiente` |

**Margen:** la agenda tiene unos 10 minutos de holgura repartidos. Si vas tarde, recorta el catálogo (bloque 2:20), nunca las demos.

---

## 0:00–0:15 · Apertura
- Pregunta al grupo (respuestas en el chat): **«¿Qué es lo primero que se rompe cuando un piloto de IA llega a producción?»**
  Suelen decir el coste, los permisos o los datos. Anótalas: hoy veremos las tres.
- La escena: Laura escribe a TiendaNova por la web y por WhatsApp. Quiere saber dónde está su pedido y si puede devolver otro.
- Las reglas del juego: antes de cada ejecución hay un **✋ Predice**. Escribe tu apuesta en el chat *antes* de que se ejecute.

## 0:15–0:40 · El mapa del agente
Abre `teoria/index.html` y pulsa los componentes. La analogía es un ordenador: modelo = procesador y ROM; contexto = RAM;
herramientas = periféricos; memoria = disco…

- **«En tu máquina»:** 11 de los 15 componentes funcionan en un portátil. Pregunta: «¿cuáles se apagan?» (son **cuatro**).
- **«En Internet»:** cada componente enseña su servicio de AWS. Este es el catálogo completo que verán hoy.
- Amazon Bedrock y los *inference profiles*: `eu.` mantiene los datos en la UE; `global.` puede salir de ella.

## 0:40–1:25 · Demo 1 · Nace en tu máquina
1. **✋** «¿Cuántos días tengo para devolver?». Recoge apuestas y ejecuta el modelo solo.
   - *Esperado:* «14 días» (mínimo legal UE), o una respuesta genérica. TiendaNova da **30**.
   - *Si contesta otra cosa:* la idea es la misma: el modelo no conoce tu negocio. Ábrelo a debate.
   - 🔍 La celda siguiente **clasifica la cifra con código** (14, 30, otra o ninguna): cuenta la rama que haya salido; la lección no depende de la cifra.
   - 🧭 `cap01`: dónde se rompe la analogía de la ROM (el modelo reconstruye, no recuerda literalmente).
2. Enseña `agent/herramientas.py` (2 minutos, sin leer línea a línea). El *docstring* **es** lo que lee el modelo para elegir.
   Ejecuta con herramientas: ahora dice 30 días y calcula 84,95 € (89,90 − 4,95).
3. **✋** «¿Convencerá Marcos al agente?». *Esperado:* no; la herramienta no le deja ver el pedido de Laura.
   - 🔍 La celda siguiente llama a la herramienta **directamente como C-002**, sin modelo: error. Convenza o no Marcos a la conversación, lo que decide es el código.
   - **Mensaje clave:** el modelo puede *querer* ayudar; el código decide qué es posible. Las reglas, en código, no en el prompt.
   - 🧭 `cap02`.
4. Cierre: «Todo esto vive en mi portátil. ¿Qué pasa con 10.000 clientes a la vez?»

## 1:35–2:20 · Demo 2 · Sale a Internet
1. **La IaC (5 minutos).** Abre `infra/main.tf` y recorre los cuatro bloques: bucket del código, Memory, rol IAM, Runtime.
   - Destaca el rol: solo puede usar *su* modelo, *su* memoria y *sus* logs.
   - Destaca que el namespace de Memory se define **una vez** y lo leen la estrategia y el agente.
   - No hace falta Docker: el código va en un zip.
2. **✋** Misma sesión frente a sesión nueva. *Esperado:* recuerda en la misma sesión y no en la nueva.
   - **Precisión importante:** Runtime **sí** devuelve la misma sesión a la misma microVM. Somos *nosotros* quienes creamos
     un `Agent` nuevo por invocación para no mezclar clientes. La continuidad la pone Memory, fuera de la microVM.
   - 🧭 `cap03` (aislamiento por sesión) y `cap04` (dónde vive la conversación).
3. **✋** «¿Recordará mañana que Laura prefiere WhatsApp?». La extracción tarda de 30 s a 2 min.
   **Mientras esperas**, explica las estrategias de memoria (preferencias, hechos, resúmenes, episodios) en `cap05`.
   - *Esperado:* sí, en una sesión nueva.
   - **Riesgo a nombrar:** el envenenamiento de memoria. Lo que el cliente dice se convierte en recuerdo; la memoria es contexto, no autoridad.

## 2:20–3:05 · El resto del catálogo (3–4 minutos por servicio)
Una página interactiva por componente; pulsa el interruptor «En tu máquina / En Internet» en cada una.

| Servicio | Página | La idea en una frase |
|---|---|---|
| Gateway + MCP | `cap07` | Tus APIs y Lambdas como herramientas MCP, con autenticación, para cualquier agente |
| Biblioteca (RAG) | `cap08` | Documentos con índice vectorial (S3 Vectors), versiones y linaje |
| Identity | `cap09` | Quién es el cliente (entrada) y con qué credenciales actúa el agente (salida) |
| Policy + Guardrails | `cap10` | Cedar fuera del agente, **deny por defecto**; Guardrails para datos sensibles e inyecciones |
| Code Interpreter (+ Browser) | `cap11` | Cálculos exactos en un *sandbox*, no «de cabeza» |
| Observability + Evaluations | `cap12` | Trazas de cada paso y jueces que puntúan la calidad |
| A/B testing | `cap13` | «Diferente» no es «mejor»: experimentos con intervalos de confianza |
| Multiagente | `cap14` | Equipos de agentes (grafo o enjambre): más calidad, más coste |
| Operación | `cap15` | Versiones, endpoints, entornos, apagado ordenado |

Menciona también, sin página: **Registry** (catálogo de agentes y herramientas), **Payments** (pagos por el agente),
**Web Search** y el ***harness* gestionado** (agente configurado sin código propio).

## 3:15–3:40 · Coste, operación y decisión
- Ejecuta el taxímetro del notebook: tokens reales de la demo. Abre `cap06`: el contexto crece en cada turno y el coste con él.
- Consola: el Runtime y sus versiones; la Memory y los registros de Laura; CloudWatch GenAI Observability, si está activado.
- **¿Cuándo AgentCore?** Cuando necesitas aislamiento por sesión, memoria gestionada, identidad y políticas sin construirlas tú.
  **¿Cuándo no?** Un prototipo interno de un solo usuario, o si ya tienes esa plataforma montada (ECS/Lambda + tu propia memoria).
- Apaga en directo: la última celda del notebook ejecuta `terraform destroy` (pide escribir DESTRUIR), o `terraform -chdir=infra destroy` en un terminal. La IaC también sirve para apagar.

## 3:40–4:00 · Preguntas y siguiente paso
- Vuelve a las respuestas de la apertura: ¿cuáles hemos visto resolver?
- El repositorio: cómo repetir la demo en su cuenta, desde Google Colab sin instalar nada o en local con Terraform (`README.md`, `PREREQUISITOS.md` §2).
- El [curso completo](https://farithjhg.github.io/aws-bedrock-agentcore-course/v7_aprender_haciendo/) (3,5 días, aprender haciendo): los 15 componentes, construidos uno a uno, con sus 18 notebooks en Colab.

---

## Si algo falla en directo
| Síntoma | Qué hacer |
|---|---|
| `ExpiredToken` / `UnrecognizedClient` | En local: `aws sso login` en el terminal del notebook y reinicia el kernel. En Colab: copia las credenciales nuevas en los Secretos y repite la celda ☁️ |
| Colab desconecta la sesión | Repite la celda ☁️: recupera el estado de Terraform de Drive; los recursos de AWS siguen donde estaban |
| `ValidationException` sobre el modelo | `model_id` no es un perfil `eu.`, o falta el formulario de Anthropic |
| `ThrottlingException` | Espera 30 s y repite; con 26 personas mirando, sigue con el vídeo grabado |
| La preferencia no aparece tras 2 min | Sigue con el catálogo y vuelve al final; la extracción a veces tarda más |
| El Runtime da 5xx | Logs en CloudWatch: `/aws/bedrock-agentcore/runtimes/…`; mientras tanto, pon el vídeo |
