# El terreno de la cuenta, con Terraform

Lo que el administrador prepara **una vez por cuenta sandbox** antes del curso (la Parte A del capítulo 0), en un solo `apply`:

| Recurso | Para qué | Variable |
|---|---|---|
| Presupuesto mensual con alertas al 50 %, 80 % y 100 % previsto | Que nadie se lleve una sorpresa en la factura | `presupuesto_usd`, `email_alertas` |
| CloudWatch Transaction Search (trazas de X-Ray a CloudWatch Logs, indexadas al 100 %) | AgentCore Observability y Evaluations: capítulos 12, 13 y 15 | `observabilidad` |
| Bucket S3 del laboratorio, *table bucket* de S3 Tables con el namespace `tiendanova` y el catálogo federado `s3tablescatalog` | La plataforma de datos de TiendaNova, que en la historia existe antes que el agente | (siempre) |
| Etiquetas de asignación de costes de la AgentCore CLI | Ver el coste por proyecto en Cost Explorer | `etiquetas_coste` |

Lo que **no** es Terraform y sigue en el capítulo 0: las cuotas de Bedrock (B5b), el formulario de caso de uso del modelo (primera invocación) y el *bootstrap* de CDK, que la AgentCore CLI hace sola en el primer `deploy`.

## Una cuenta

```
cd infra/cuenta
cp terraform.tfvars.example terraform.tfvars      # y rellénalo
terraform init
terraform apply
```

El participante no necesita el estado ni las salidas: al empezar el capítulo 0, `terreno()` encuentra los recursos por su nombre (`nova-datos-<cuenta>`, `nova-lab-<cuenta>-<región>`, `s3tablescatalog`, `nova-assist-lab`) y los apunta en `lab_state.json`.

## Varias cuentas

Un estado por cuenta y un perfil de AWS por cuenta. Con los perfiles `nova-01`, `nova-02`… en `~/.aws/config`:

```bash
# bash
terraform init
for p in nova-01 nova-02 nova-03; do
  AWS_PROFILE=$p terraform apply -state="estados/$p.tfstate" -var "cuenta_esperada=$(AWS_PROFILE=$p aws sts get-caller-identity --query Account --output text)" -auto-approve
done
```

```powershell
# PowerShell
terraform init
foreach ($p in "nova-01","nova-02","nova-03") {
  $env:AWS_PROFILE = $p
  $cuenta = aws sts get-caller-identity --query Account --output text
  terraform apply -state="estados/$p.tfstate" -var "cuenta_esperada=$cuenta" -auto-approve
}
```

Para apagar, lo mismo con `destroy`. Los estados van en `estados/` (ignorado por git): guárdalos, son lo que sabe qué borrar.

## Si una SCP bloquea Transaction Search

El `plan` lo dice antes de tocar nada: son tres acciones, `logs:PutResourcePolicy`, `xray:UpdateTraceSegmentDestination` y `xray:UpdateIndexingRule`. O la organización las permite en las cuentas del curso, o quien administra la organización ejecuta este `apply`, o se pone `observabilidad = false`: entonces funcionan los capítulos 0 a 11, 14, 16 y 17, y los capítulos 12, 13 y 15 (Observability, Evaluations, A/B y la puerta de calidad) no pueden evaluar.

## Apagar

`terraform destroy` borra el presupuesto, desactiva Transaction Search (el destino vuelve a X-Ray y se retira la política), borra el catálogo y los buckets **con todo lo que tengan** (las tablas Iceberg y los documentos). Antes, cada participante ejecuta el capítulo 17, que borra lo que creó la CLI y los notebooks. Si la cuenta se va a reutilizar en otra edición, no hace falta destruir: la Parte C del capítulo 0 recarga los datos.
