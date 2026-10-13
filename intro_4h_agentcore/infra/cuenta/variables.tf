variable "region" {
  description = "Región de AWS: la misma que en ../terraform.tfvars (eu-west-1 tiene Runtime y Memory)."
  type        = string
  default     = "eu-west-1"
}

variable "cuenta_esperada" {
  description = "ID de la cuenta sandbox, como protección frente a aplicar en la equivocada. Vacío = sin comprobación."
  type        = string
  default     = ""
}

variable "presupuesto_usd" {
  description = "Presupuesto mensual con alertas (0 = sin presupuesto)."
  type        = number
  default     = 20
}

variable "email_alertas" {
  description = "Destinatario de las alertas de presupuesto."
  type        = string
  default     = ""
}

variable "observabilidad" {
  description = "Transaction Search, para ver las sesiones en CloudWatch GenAI Observability (parte 3 de la demo). Opcional: cuesta por traza indexada y una SCP puede bloquearlo."
  type        = bool
  default     = false
}
