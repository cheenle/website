variable "hosts" {
  description = "Managed hosts. Key is alias used by Terraform and SSH config."
  type = map(object({
    host             = string
    user             = string
    port             = number
    private_key_path = string
    enabled          = bool
    tags             = list(string)
  }))

  default = {
    p6 = {
      host             = "p6.vlsc.net"
      user             = "cheenle"
      port             = 22
      private_key_path = ""
      enabled          = true
      tags             = ["remote", "linux"]
    }
    ham = {
      host             = "ham.vlsc.net"
      user             = "cheenle"
      port             = 22
      private_key_path = ""
      enabled          = true
      tags             = ["remote", "linux"]
    }
    mule = {
      host             = "mule.vlsc.net"
      user             = "mulerun"
      port             = 22
      private_key_path = ""
      enabled          = true
      tags             = ["remote", "linux"]
    }
    www = {
      host             = "www.vlsc.net"
      user             = "cheenle"
      port             = 22
      private_key_path = ""
      enabled          = true
      tags             = ["remote", "web", "ipv4", "ipv6"]
    }
    local_1 = {
      host             = "192.168.1.10"
      user             = "pi"
      port             = 22
      private_key_path = ""
      enabled          = false
      tags             = ["local", "linux"]
    }
    local_2 = {
      host             = "192.168.1.11"
      user             = "pi"
      port             = 22
      private_key_path = ""
      enabled          = false
      tags             = ["local", "linux"]
    }
  }
}

variable "command_profiles" {
  description = "Reusable command profiles executed on each enabled host."
  type        = map(list(string))
  default = {
    probe = [
      "echo '--- host: '$(hostname)",
      "uname -a",
      "uptime",
    ]
    update_debian = [
      "sudo apt-get update -y",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y",
    ]
    nginx_reload = [
      "sudo nginx -t",
      "sudo systemctl reload nginx",
    ]
  }
}

variable "command_profile" {
  description = "Which command profile to execute."
  type        = string
  default     = "probe"

  validation {
    condition     = contains(keys(var.command_profiles), var.command_profile)
    error_message = "command_profile must exist in command_profiles."
  }
}

variable "connection_timeout" {
  description = "SSH connection timeout for remote-exec."
  type        = string
  default     = "20s"
}
