variable "region" {
  description = "Región de la formación. eu-west-1 tiene todo lo que usa el curso; Madrid (eu-south-2) tiene Runtime pero no Memory."
  type        = string
  default     = "eu-west-1"
}

variable "cuenta_esperada" {
  description = "ID de la cuenta sandbox. Protección frente a aplicar en la cuenta equivocada: si no coincide con las credenciales, el plan falla. Vacío = sin comprobación."
  type        = string
  default     = ""
}

variable "presupuesto_usd" {
  description = "Presupuesto mensual con alertas (0 = sin presupuesto)."
  type        = number
  default     = 50
}

variable "email_alertas" {
  description = "Destinatario de las alertas de presupuesto."
  type        = string
  default     = ""
}

variable "observabilidad" {
  description = "Transaction Search. Necesario para los capítulos 12, 13 y 15. Si una SCP lo bloquea, false: el resto del curso funciona."
  type        = bool
  default     = true
}

variable "etiquetas_coste" {
  description = "Etiquetas de asignación de costes de la CLI (segundo apply, tras el primer despliegue)."
  type        = bool
  default     = false
}
