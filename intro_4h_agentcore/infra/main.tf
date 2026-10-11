data "aws_caller_identity" "actual" {}
data "aws_partition" "actual" {}

locals {
  cuenta    = data.aws_caller_identity.actual.account_id
  particion = data.aws_partition.actual.partition
  # Una sola fuente de verdad para el namespace: la estrategia de Memory y el agente usan la misma.
  plantilla_preferencias = "/users/{actorId}/preferences"
  zip_agente             = "${path.module}/../build/agent.zip"
}

# ---------------------------------------------------------------------------------------
# Artefacto: el código del agente, empaquetado como zip (sin Docker) por scripts/empaquetar.py
# ---------------------------------------------------------------------------------------
resource "aws_s3_bucket" "artefactos" {
  bucket        = "tiendanova-intro-${local.cuenta}-${var.region}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "artefactos" {
  bucket                  = aws_s3_bucket.artefactos.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "artefactos" {
  bucket = aws_s3_bucket.artefactos.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_object" "agente" {
  bucket      = aws_s3_bucket.artefactos.id
  key         = "agente/agent.zip"
  source      = local.zip_agente
  source_hash = filemd5(local.zip_agente)
  depends_on  = [aws_s3_bucket_versioning.artefactos]
}

# ---------------------------------------------------------------------------------------
# AgentCore Memory: corto plazo (eventos de la sesión) + largo plazo (preferencias del cliente)
# ---------------------------------------------------------------------------------------
resource "aws_bedrockagentcore_memory" "nova" {
  name                  = "${var.nombre}_memoria"
  description           = "Memoria de Nova Assist (demo de introducción)"
  event_expiry_duration = var.dias_retencion_eventos
}

resource "aws_bedrockagentcore_memory_strategy" "preferencias" {
  memory_id           = aws_bedrockagentcore_memory.nova.id
  name                = "preferencias_cliente"
  description         = "Extrae preferencias del cliente (canal de contacto, horarios...)"
  type                = "USER_PREFERENCE"
  namespace_templates = [local.plantilla_preferencias]
}

# ---------------------------------------------------------------------------------------
# Rol de ejecución del Runtime: solo lo que el agente necesita
# ---------------------------------------------------------------------------------------
data "aws_iam_policy_document" "confianza_runtime" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["bedrock-agentcore.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.cuenta]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:${local.particion}:bedrock-agentcore:${var.region}:${local.cuenta}:*"]
    }
  }
}

data "aws_iam_policy_document" "permisos_runtime" {
  statement {
    sid     = "Modelo"
    actions = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = [
      "arn:${local.particion}:bedrock:${var.region}:${local.cuenta}:inference-profile/${var.model_id}",
      # El perfil eu. enruta a varias regiones de la UE: el modelo base se invoca en cualquiera de ellas.
      "arn:${local.particion}:bedrock:*::foundation-model/*",
    ]
  }
  statement {
    sid = "Memoria"
    actions = [
      "bedrock-agentcore:CreateEvent", "bedrock-agentcore:GetEvent", "bedrock-agentcore:ListEvents",
      "bedrock-agentcore:ListSessions", "bedrock-agentcore:RetrieveMemoryRecords",
      "bedrock-agentcore:ListMemoryRecords", "bedrock-agentcore:GetMemoryRecord",
    ]
    resources = [aws_bedrockagentcore_memory.nova.arn]
  }
  statement {
    sid       = "Codigo"
    actions   = ["s3:GetObject", "s3:GetObjectVersion"]
    resources = ["${aws_s3_bucket.artefactos.arn}/*"]
  }
  statement {
    sid = "Logs"
    actions = [
      "logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents",
      "logs:DescribeLogStreams", "logs:DescribeLogGroups",
    ]
    resources = ["arn:${local.particion}:logs:${var.region}:${local.cuenta}:log-group:/aws/bedrock-agentcore/runtimes/*"]
  }
  statement {
    sid       = "Trazas"
    actions   = ["xray:PutTraceSegments", "xray:PutTelemetryRecords", "xray:GetSamplingRules", "xray:GetSamplingTargets"]
    resources = ["*"]
  }
  statement {
    sid       = "Metricas"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["bedrock-agentcore"]
    }
  }
  statement {
    sid     = "IdentidadDeCarga"
    actions = ["bedrock-agentcore:GetWorkloadAccessToken", "bedrock-agentcore:GetWorkloadAccessTokenForJWT", "bedrock-agentcore:GetWorkloadAccessTokenForUserId"]
    resources = [
      "arn:${local.particion}:bedrock-agentcore:${var.region}:${local.cuenta}:workload-identity-directory/default",
      "arn:${local.particion}:bedrock-agentcore:${var.region}:${local.cuenta}:workload-identity-directory/default/workload-identity/*",
    ]
  }
}

resource "aws_iam_role" "runtime" {
  name               = "${var.nombre}-runtime"
  assume_role_policy = data.aws_iam_policy_document.confianza_runtime.json
}

resource "aws_iam_role_policy" "runtime" {
  name   = "permisos-agente"
  role   = aws_iam_role.runtime.id
  policy = data.aws_iam_policy_document.permisos_runtime.json
}

# ---------------------------------------------------------------------------------------
# AgentCore Runtime: el agente, servido en microVMs aisladas por sesión
# ---------------------------------------------------------------------------------------
resource "aws_bedrockagentcore_agent_runtime" "nova" {
  agent_runtime_name = "${var.nombre}_agente"
  description        = "Nova Assist: agente de atención al cliente de TiendaNova"
  role_arn           = aws_iam_role.runtime.arn

  agent_runtime_artifact {
    code_configuration {
      entry_point = ["main.py"]
      runtime     = "PYTHON_3_13"
      code {
        s3 {
          bucket     = aws_s3_bucket.artefactos.id
          prefix     = aws_s3_object.agente.key
          version_id = aws_s3_object.agente.version_id # un zip nuevo crea una versión nueva del Runtime
        }
      }
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  environment_variables = {
    MODEL_ID                 = var.model_id
    MEMORY_ID                = aws_bedrockagentcore_memory.nova.id
    PREFS_NAMESPACE_TEMPLATE = local.plantilla_preferencias
  }

  depends_on = [aws_iam_role_policy.runtime, aws_bedrockagentcore_memory_strategy.preferencias]
}
