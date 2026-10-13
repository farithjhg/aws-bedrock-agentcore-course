# El terreno de la cuenta para la intro de 4 horas: presupuesto con alertas y, si se quiere, Transaction Search
# para la vista de la consola de la parte 3. Reutiliza el módulo del curso completo (mismo repositorio).
#
#   cd infra/cuenta && terraform init && terraform apply -var email_alertas=tu@correo
#
# Es una pila aparte de la demo (../): el presupuesto y Transaction Search son de la cuenta, no de la demo,
# y no deben caerse con `terraform -chdir=infra destroy`.

data "aws_caller_identity" "actual" {}

resource "terraform_data" "guardia" {
  input = data.aws_caller_identity.actual.account_id

  lifecycle {
    precondition {
      condition     = var.cuenta_esperada == "" || data.aws_caller_identity.actual.account_id == var.cuenta_esperada
      error_message = "Las credenciales son de la cuenta ${data.aws_caller_identity.actual.account_id}, no de ${var.cuenta_esperada}."
    }
  }
}

module "cuenta" {
  source = "../../../v7_aprender_haciendo/infra/modulos/cuenta"

  nombre           = "tiendanova-intro"
  presupuesto_usd  = var.presupuesto_usd
  email_alertas    = var.email_alertas
  observabilidad   = var.observabilidad
  plataforma_datos = false # la demo no usa S3 Tables: sus datos de ejemplo van dentro del agente

  depends_on = [terraform_data.guardia]
}
