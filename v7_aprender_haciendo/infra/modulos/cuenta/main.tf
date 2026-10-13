# El terreno de una cuenta sandbox para el curso Nova Assist: lo que antes hacía a mano el administrador en la
# Parte A del capítulo 0. Módulo compartido por el curso completo (v7_aprender_haciendo) y la intro de 4 horas.
# Sin bloque provider: lo pone la raíz que lo usa (infra/cuenta de cada carpeta).

data "aws_caller_identity" "actual" {}
data "aws_partition" "actual" {}
data "aws_region" "actual" {}

locals {
  cuenta    = data.aws_caller_identity.actual.account_id
  particion = data.aws_partition.actual.partition
  region    = data.aws_region.actual.region
}

# ---------------------------------------------------------------------------------------
# Presupuesto con alertas (los presupuestos viven en us-east-1: lo resuelve el servicio, no hace falta otro provider)
# ---------------------------------------------------------------------------------------
resource "aws_budgets_budget" "lab" {
  count = var.presupuesto_usd > 0 ? 1 : 0

  name         = "${var.nombre}-assist-lab"
  budget_type  = "COST"
  limit_amount = tostring(var.presupuesto_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = [["ACTUAL", 50], ["ACTUAL", 80], ["FORECASTED", 100]]
    content {
      notification_type          = notification.value[0]
      threshold                  = notification.value[1]
      threshold_type             = "PERCENTAGE"
      comparison_operator        = "GREATER_THAN"
      subscriber_email_addresses = [var.email_alertas]
    }
  }

  lifecycle {
    precondition {
      condition     = var.email_alertas != ""
      error_message = "Con presupuesto hace falta email_alertas (o pon presupuesto_usd = 0)."
    }
  }
}

# ---------------------------------------------------------------------------------------
# CloudWatch Transaction Search: requisito de AgentCore Observability y Evaluations.
# Son las tres acciones que una SCP puede bloquear: logs:PutResourcePolicy, xray:UpdateTraceSegmentDestination
# y xray:UpdateIndexingRule. Si la organización no las permite, observabilidad = false.
# ---------------------------------------------------------------------------------------
data "aws_iam_policy_document" "transaction_search" {
  count = var.observabilidad ? 1 : 0

  statement {
    sid     = "TransactionSearchXRayAccess"
    actions = ["logs:PutLogEvents"]
    principals {
      type        = "Service"
      identifiers = ["xray.amazonaws.com"]
    }
    resources = [
      "arn:${local.particion}:logs:${local.region}:${local.cuenta}:log-group:aws/spans:*",
      "arn:${local.particion}:logs:${local.region}:${local.cuenta}:log-group:/aws/application-signals/data:*",
    ]
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:${local.particion}:xray:${local.region}:${local.cuenta}:*"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.cuenta]
    }
  }
}

resource "aws_cloudwatch_log_resource_policy" "transaction_search" {
  count = var.observabilidad ? 1 : 0

  policy_name     = "NovaLabTransactionSearch"
  policy_document = data.aws_iam_policy_document.transaction_search[0].json
}

resource "aws_xray_trace_segment_destination" "cloudwatch" {
  count = var.observabilidad ? 1 : 0

  destination = "CloudWatchLogs"
  depends_on  = [aws_cloudwatch_log_resource_policy.transaction_search]
}

resource "aws_xray_indexing_rule" "laboratorio" {
  count = var.observabilidad ? 1 : 0

  name = "Default"
  rule {
    probabilistic {
      desired_sampling_percentage = var.muestreo_indexacion
    }
  }
  depends_on = [aws_xray_trace_segment_destination.cloudwatch]
}

# ---------------------------------------------------------------------------------------
# Plataforma de datos de TiendaNova: en la historia existe antes que el agente
# ---------------------------------------------------------------------------------------
resource "aws_s3_bucket" "lab" {
  count = var.plataforma_datos ? 1 : 0

  bucket        = "${var.nombre}-lab-${local.cuenta}-${local.region}"
  force_destroy = true # documentos de políticas y resultados de Athena: se borran con la cuenta del laboratorio
}

resource "aws_s3_bucket_public_access_block" "lab" {
  count = var.plataforma_datos ? 1 : 0

  bucket                  = aws_s3_bucket.lab[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3tables_table_bucket" "datos" {
  count = var.plataforma_datos ? 1 : 0

  name          = "${var.nombre}-datos-${local.cuenta}"
  force_destroy = true # las tablas Iceberg que cargan los notebooks se borran con el table bucket
}

resource "aws_s3tables_namespace" "tiendanova" {
  count = var.plataforma_datos ? 1 : 0

  namespace        = var.namespace
  table_bucket_arn = aws_s3tables_table_bucket.datos[0].arn
}

# Catálogo federado: Athena (y la Lambda de pedidos del capítulo 7) ven las tablas de S3 Tables como
# s3tablescatalog/<table bucket>. Uno por cuenta y región, con control de acceso por IAM.
resource "aws_glue_catalog" "s3tables" {
  count = var.plataforma_datos ? 1 : 0

  name = "s3tablescatalog"
  federated_catalog {
    connection_name = "aws:s3tables"
    identifier      = "arn:${local.particion}:s3tables:${local.region}:${local.cuenta}:bucket/*"
  }
  allow_full_table_external_data_access = "True"
}

# ---------------------------------------------------------------------------------------
# Etiquetas de asignación de costes de la AgentCore CLI (segundo apply, cuando ya aparecen en la facturación)
# ---------------------------------------------------------------------------------------
resource "aws_ce_cost_allocation_tag" "agentcore" {
  for_each = var.etiquetas_coste ? toset(["agentcore:project-name", "agentcore:created-by"]) : toset([])

  tag_key = each.value
  status  = "Active"
}
