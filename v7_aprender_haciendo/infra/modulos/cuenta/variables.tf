variable "nombre" {
  description = "Prefijo de los recursos del laboratorio (minúsculas, números y guiones)."
  type        = string
  default     = "nova"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,20}$", var.nombre))
    error_message = "Empieza por letra; solo minúsculas, números y guiones (máx. 21 caracteres)."
  }
}

variable "presupuesto_usd" {
  description = "Presupuesto mensual de la cuenta para la formación, con alertas al 50 %, 80 % y 100 % previsto. 0 = sin presupuesto."
  type        = number
  default     = 50
}

variable "email_alertas" {
  description = "Destinatario de las alertas del presupuesto (obligatorio si presupuesto_usd > 0)."
  type        = string
  default     = ""
  validation {
    condition     = var.email_alertas == "" || can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.email_alertas))
    error_message = "Pon una dirección de correo válida."
  }
}

variable "observabilidad" {
  description = "Activa CloudWatch Transaction Search (trazas de X-Ray a CloudWatch Logs, indexadas). Lo necesitan Observability y Evaluations (curso completo: capítulos 12, 13 y 15; intro: la vista de la consola, opcional)."
  type        = bool
  default     = true
}

variable "muestreo_indexacion" {
  description = "Porcentaje de trazas que Transaction Search indexa. 100 en el laboratorio (las evaluaciones las necesitan todas); en producción, un valor bajo: cada traza indexada se paga."
  type        = number
  default     = 100
}

variable "plataforma_datos" {
  description = "Crea la plataforma de datos de TiendaNova: bucket S3 del laboratorio, table bucket de S3 Tables con el namespace Iceberg y el catálogo federado s3tablescatalog para Athena."
  type        = bool
  default     = true
}

variable "namespace" {
  description = "Namespace Iceberg de las tablas de TiendaNova."
  type        = string
  default     = "tiendanova"
}

variable "etiquetas_coste" {
  description = "Activa como etiquetas de asignación de costes las que pone la AgentCore CLI (agentcore:project-name, agentcore:created-by). Solo funciona cuando ya han aparecido en la facturación: actívalo en un segundo apply, tras el primer despliegue."
  type        = bool
  default     = false
}
