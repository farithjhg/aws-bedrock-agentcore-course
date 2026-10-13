# Las mismas claves que escribe `terreno()` en lab_state.json cuando el participante empieza el capítulo 0
output "cuenta" { value = module.cuenta.cuenta }
output "region" { value = module.cuenta.region }
output "presupuesto" { value = module.cuenta.presupuesto }
output "observabilidad" { value = module.cuenta.observabilidad }
output "lab_bucket" { value = module.cuenta.lab_bucket }
output "table_bucket" { value = module.cuenta.table_bucket }
output "table_bucket_arn" { value = module.cuenta.table_bucket_arn }
output "namespace" { value = module.cuenta.namespace }
output "athena_catalog" { value = module.cuenta.athena_catalog }
output "athena_output" { value = module.cuenta.athena_output }
