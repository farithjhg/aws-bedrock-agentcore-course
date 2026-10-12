output "region" {
  value = var.region
}

output "agent_runtime_arn" {
  description = "ARN del agente desplegado (lo leen scripts/nova.py y la demo)"
  value       = aws_bedrockagentcore_agent_runtime.nova.agent_runtime_arn
}

output "memory_id" {
  value = aws_bedrockagentcore_memory.nova.id
}

output "namespace_preferencias" {
  value = local.plantilla_preferencias
}

output "model_id" {
  value = var.model_id
}
