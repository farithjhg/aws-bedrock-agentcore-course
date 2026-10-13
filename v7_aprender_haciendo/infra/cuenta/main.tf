# El terreno del curso completo: un `terraform apply` por cuenta sandbox deja la cuenta lista para los capítulos 0–17,
# y `terraform destroy` la devuelve a como estaba. Es la Parte A del capítulo 0.
#
#   cd infra/cuenta
#   cp terraform.tfvars.example terraform.tfvars    # y rellénalo
#   terraform init
#   terraform apply
#
# Varias cuentas: un estado por cuenta (ver README.md).

data "aws_caller_identity" "actual" {}

resource "terraform_data" "guardia" {
  input = data.aws_caller_identity.actual.account_id

  lifecycle {
    precondition {
      condition     = var.cuenta_esperada == "" || data.aws_caller_identity.actual.account_id == var.cuenta_esperada
      error_message = "Las credenciales son de la cuenta ${data.aws_caller_identity.actual.account_id}, no de ${var.cuenta_esperada}. Revisa el perfil de AWS o cuenta_esperada."
    }
  }
}

module "cuenta" {
  source = "../modulos/cuenta"

  presupuesto_usd  = var.presupuesto_usd
  email_alertas    = var.email_alertas
  observabilidad   = var.observabilidad
  plataforma_datos = true
  etiquetas_coste  = var.etiquetas_coste

  depends_on = [terraform_data.guardia]
}
