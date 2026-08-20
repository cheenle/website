# Terraform 主机管理

这个目录用 Terraform 统一管理本地与远程 Linux 主机（通过 SSH 执行命令）。

默认 inventory 包含：
- `p6.vlsc.net`
- `ham.vlsc.net`
- `mulerun@mule.vlsc.net`
- `www.vlsc.net`（标签包含 `ipv4` / `ipv6`）
- `local_1` / `local_2`（本地主机示例，默认 `enabled=false`）

## 1) 准备变量

```bash
cd /Users/cheenle/HAM/website/manage
cp terraform.tfvars.example terraform.tfvars
```

编辑 `terraform.tfvars`：
- SSH 用户、端口
- `private_key_path`（留空则使用 SSH agent）
- 每台主机的 `enabled = true/false`

## 2) 初始化

```bash
terraform init
```

## 3) 执行命令 profile

默认是 `probe`（探测）：

```bash
terraform apply
```

切换为其它 profile：

```bash
terraform apply -var='command_profile=update_debian'
terraform apply -var='command_profile=nginx_reload'
```

## 4) 自定义命令 profile

在 `terraform.tfvars` 中覆盖：

```hcl
command_profiles = {
  probe = [
    "hostname",
    "uptime",
  ]
  web_deploy_check = [
    "sudo nginx -t",
    "ls -lah /var/www/vlsc.net",
  ]
}
command_profile = "web_deploy_check"
```

## 5) 生成 SSH config

Terraform 会生成：
- `ssh_config.generated`

直接使用：

```bash
ssh -F ssh_config.generated www
ssh -F ssh_config.generated mule
```

## 说明

- 当前方案基于 `null_resource` + `remote-exec`。
- 适合统一探测、批量执行运维命令、基础配置操作。
- 后续若要做更复杂的配置管理，可叠加 Ansible。
