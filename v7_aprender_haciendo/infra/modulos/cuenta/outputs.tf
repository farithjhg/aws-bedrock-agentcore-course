output "cuenta" {
  value = local.cuenta
}

output "region" {
  value = local.region
}

output "presupuesto" {
  description = "Nombre del presupuesto (BUDGET_NAME en lab_state.json)."
  value       = try(aws_budgets_budget.lab[0].name, null)
}

output "observabilidad" {
  description = "true si Transaction Search quedó activo (capítulos 12, 13 y 15 del curso completo)."
  value       = var.observabilidad
}

output "lab_bucket" {
  description = "Bucket S3 del laboratorio (LAB_BUCKET): documentos de políticas y resultados de Athena."
  value       = try(aws_s3_bucket.lab[0].bucket, null)
}

output "table_bucket" {
  value = try(aws_s3tables_table_bucket.datos[0].name, null)
}

output "table_bucket_arn" {
  description = "ARN del table bucket de S3 Tables (TABLE_BUCKET_ARN): el warehouse de PyIceberg."
  value       = try(aws_s3tables_table_bucket.datos[0].arn, null)
}

output "namespace" {
  value = try(aws_s3tables_namespace.tiendanova[0].namespace, null)
}

output "athena_catalog" {
  description = "Catálogo que usa Athena para ver las tablas (ATHENA_CATALOG)."
  value       = try("s3tablescatalog/${aws_s3tables_table_bucket.datos[0].name}", null)
}

output "athena_output" {
  description = "Dónde deja Athena los resultados (ATHENA_OUTPUT)."
  value       = try("s3://${aws_s3_bucket.lab[0].bucket}/athena/", null)
}
