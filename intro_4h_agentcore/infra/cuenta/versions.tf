terraform {
  required_version = ">= 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.68"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      proyecto = "tiendanova-intro-agentcore"
    }
  }
}
