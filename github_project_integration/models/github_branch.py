from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import subprocess


class GitHubBranch(models.Model):
    _name = 'github.branch'
    _description = 'Ramas del Repositorio GitHub'

    name = fields.Char(string='Nombre de la Rama', required=True)
    project_id = fields.Many2one('project.project', string='Proyecto Relacionado', required=True)
    commit_sha = fields.Char(string='SHA del Commit', readonly=True)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    branch_id = fields.Many2one('github.branch', string='Rama')
    branch_destination_id = fields.Many2one('github.branch', string='Rama destino')
    has_pr_pending = fields.Boolean(string="Tiene PR Pendiente", readonly=True)
    pr_url = fields.Char(string="URL del Pull Request", readonly=True)

    # Campos para el PR
    title = fields.Char(string='Titulo del PR')
    def check_pending_prs(self):
        """
        Método para verificar si las ramas asociadas a las tareas tienen PR pendientes..
        """
        for record in self:
            if not record.branch_id:
                continue  # Saltar si no hay rama asociada

            github_integration = self.env['github.integration'].search([
                ('project_id', '=', record.project_id.id)
            ], limit=1)

            if not github_integration:
                continue  # Saltar si no se encuentra una integración de GitHub para el proyecto

            headers = {
                "Authorization": f"token {github_integration.access_token}",
                "Accept": "application/vnd.github.v3+json"
            }

            try:
                # Construir URL para consultar PRs de la rama
                repo_url = github_integration.repository_url.replace("https://github.com/", "")
                api_url = f"https://api.github.com/repos/{repo_url}/pulls"
                response = requests.get(api_url, headers=headers)

                if response.status_code == 200:
                    pr_list = response.json()
                    # Verificar si hay PRs abiertos para la rama
                    has_pr = any(pr['head']['ref'] == record.branch_id.name and pr['state'] == 'open' for pr in pr_list)
                    record.has_pr_pending = has_pr
                else:
                    raise UserError(_("Error al obtener PRs: %s") % response.json().get('message', ''))
            except Exception as e:
                raise UserError(_("Error al verificar PRs: %s") % str(e))

    def _cron_check_pending_prs(self):
        tasks = self.env['project.task'].search([])
        tasks.check_pending_prs()

    def action_create_pr(self):
        """
        Crea un Pull Request (PR) en GitHub para la tarea actual.
        """
        # Obtener datos de la tarea, incluyendo la rama
        for record in self:
            if not record.branch_id:
                raise UserError("La tarea no tiene una rama asociada.")

            # Variables de GitHub
            github_integration = self.env['github.integration'].search([
                ('project_id', '=', record.project_id.id)
            ], limit=1)
            if not github_integration.access_token:
                raise UserError("El proyecto no tiene un token configurado de GitHub.")

            headers = {
                "Authorization": f"token {github_integration.access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            if 'github.com' not in github_integration.repository_url:
                raise UserError(_('La URL no parece válida para un repositorio de GitHub.'))

            path_parts = github_integration.repository_url.replace("https://github.com/", "").split('/')
            if len(path_parts) < 2:
                raise UserError(_('La URL del repositorio no tiene el formato correcto.'))

            owner, repo = path_parts[0], path_parts[1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

            # Detalles del PR
            pr_data = {
                "title": record.title,
                "head": record.branch_id.name,  # La rama de origen
                "base": record.branch_destination_id.name,  # La rama de destino (puede cambiarse)
                "body": f"PR creado desde Odoo para la tarea {record.name}.",
            }

            # Crear el PR a través de la API de GitHub
            response = requests.post(api_url, json=pr_data, headers=headers)

            if response.status_code == 201:
                pr_info = response.json()
                record.write({
                    'pr_url': pr_info['html_url'],  # Almacenar el enlace del PR en la tarea
                })
                return True
            else:
                raise UserError(f"Error al crear el Pull Request: {response.json().get('message')}")

    # def check_ready_for_pr(self):
    #     """
    #     Verifica qué ramas tienen cambios pendientes para ser fusionados en un PR.
    #     """
    #     for task in self:
    #         if not task.branch_id:
    #             raise UserError("La tarea no tiene una rama asociada.")
    #
    #         branch_name = task.branch_id.name
    #         local_branches = self._get_local_branches()
    #         remote_branches = self._get_remote_branches()
    #
    #         if branch_name in local_branches and branch_name in remote_branches:
    #             # Verificar si la rama tiene cambios no fusionados
    #             if self._is_ready_for_pr(branch_name):
    #                 task.write({
    #                     'pr_status': 'Listo para PR'
    #                 })
    #             else:
    #                 task.write({
    #                     'pr_status': 'No listo para PR'
    #                 })
    #
    # def _get_local_branches(self):
    #     """
    #     Obtiene las ramas locales en el repositorio de Git.
    #     """
    #     try:
    #         result = subprocess.run(
    #             ["git", "branch", "--list"],
    #             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    #         )
    #         local_branches = result.stdout.decode('utf-8').splitlines()
    #         return [branch.strip() for branch in local_branches]
    #     except subprocess.CalledProcessError as e:
    #         raise UserError(f"Error al obtener ramas locales: {e.stderr.decode()}")
    #
    # def _get_remote_branches(self):
    #     """
    #     Obtiene las ramas remotas a través de la API de GitHub.
    #     """
    #     try:
    #         repo_owner = "OWNER_NAME"  # Reemplaza con el propietario del repositorio
    #         repo_name = "REPO_NAME"  # Reemplaza con el nombre del repositorio
    #         api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches"
    #         headers = {
    #             "Authorization": f"token YOUR_GITHUB_TOKEN",  # Reemplaza con tu token
    #             "Accept": "application/vnd.github.v3+json"
    #         }
    #         response = requests.get(api_url, headers=headers)
    #         if response.status_code == 200:
    #             branches = response.json()
    #             remote_branches = [branch['name'] for branch in branches]
    #             return remote_branches
    #         else:
    #             raise UserError(f"Error al obtener las ramas remotas: {response.json().get('message')}")
    #     except Exception as e:
    #         raise UserError(f"Error al obtener ramas remotas: {str(e)}")
    #
    # def _is_ready_for_pr(self, branch_name):
    #     """
    #     Verifica si la rama tiene cambios pendientes de fusionar.
    #     """
    #     try:
    #         # Verifica si la rama local está por delante de la rama principal
    #         result = subprocess.run(
    #             ["git", "log", f"origin/main..{branch_name}"],
    #             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    #         )
    #         # Si la salida no está vacía, la rama tiene commits no fusionados
    #         if result.stdout.decode('utf-8').strip():
    #             return True
    #         else:
    #             return False
    #     except subprocess.CalledProcessError as e:
    #         raise UserError(f"Error al verificar la rama: {e.stderr.decode()}")
