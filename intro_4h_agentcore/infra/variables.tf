variable "region" {
  description = "Región de AWS. eu-west-1 tiene Runtime y Memory; no todas las regiones europeas tienen Memory."
  type        = string
  default     = "eu-west-1"
}

variable "model_id" {
  description = "Inference profile del modelo (eu. mantiene los datos en la UE). Lista los disponibles con el comando del README."
  type        = string
  validation {
    condition     = can(regex("^(eu|global)\\.", var.model_id))
    error_message = "Usa un inference profile que empiece por 'eu.' (o 'global.'), no un modelId base."
  }
}

variable "nombre" {
  description = "Prefijo de los recursos de AgentCore (letras, números y guion bajo)."
  type        = string
  default     = "TiendaNovaIntro"
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]{0,30}$", var.nombre))
    error_message = "Empieza por letra; solo letras, números y _ (máx. 31 caracteres)."
  }
}

variable "dias_retencion_eventos" {
  description = "Días que Memory guarda los eventos de conversación (memoria a corto plazo)."
  type        = number
  default     = 7
}
