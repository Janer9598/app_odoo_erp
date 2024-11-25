import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GitHubIntegration(models.Model):
    _name = 'github.integration'
    _description = 'Integración con GitHub'

    name = fields.Char(string='Nombre del Repositorio', required=True)
    repository_url = fields.Char(string='URL del Repositorio', required=True)
    access_token = fields.Char(string='Token de Acceso', required=True)
    project_id = fields.Many2one('project.project', string='Proyecto Relacionado', readonly=True)

    repository_data = fields.Text(string='Datos del Repositorio', readonly=True)

    def fetch_repository_data(self):
        """
        Función para traer información del repositorio desde GitHub.
        """
        for record in self:  # Manejar múltiples registros
            headers = {
                "Authorization": f"token {record.access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            try:
                # Extraer owner y repo del URL
                if 'github.com' not in record.repository_url:
                    raise UserError(_('La URL no parece válida para un repositorio de GitHub.'))

                path_parts = record.repository_url.replace("https://github.com/", "").split('/')
                if len(path_parts) < 2:
                    raise UserError(_('La URL del repositorio no tiene el formato correcto.'))

                owner, repo = path_parts[0], path_parts[1]
                api_url = f"https://api.github.com/repos/{owner}/{repo}"

                response = requests.get(api_url, headers=headers)
                if response.status_code == 200:
                    # Guardar los datos del repositorio
                    repo_data = response.json()
                    record.repository_data = repo_data

                    # Crear proyecto en Odoo
                    project_values = {
                        'name': repo_data.get('name'),
                        'description': repo_data.get('description', 'Sin descripción'),
                        'user_id': self.env.uid,  # Asignar al usuario actual
                    }
                    project = self.env['project.project'].create(project_values)

                    etapas = ['DEVELOPER', 'PULL REQUEST', 'MARGE']

                    '''
                    Falta realizar pruebas de las etapas del proyecto
                    '''
                    project_type = ''
                    for etapa in etapas:
                        etapas_values = {
                            'name': etapa,
                            'project_ids': [(6, 0, project.id)],
                            'user_id': self.env.uid,  # Asignar al usuario actual
                        }
                        project_type = self.env['project.task.type'].create(etapas_values)

                    # Relacionar el proyecto creado con el registro
                    record.project_id = project.id
                    self.fetch_repository_branches(headers, project, path_parts, project_type)
                else:
                    raise UserError(_(f"Error al conectar con GitHub: {response.json().get('message')}"))

            except Exception as e:
                raise UserError(_(f"Ocurrió un error: {str(e)}"))

    def fetch_repository_branches(self, headers, project, path_parts, project_type):
        """
        Obtener las ramas del repositorio desde GitHub y vincularlas al proyecto.
        """
        if not project:
            raise UserError(_('No hay un proyecto vinculado al repositorio.'))

        try:
            owner, repo = path_parts[0], path_parts[1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}/branches"

            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                branches = response.json()

                for branch in branches:
                    # Crear rama en el modelo `github.branch`
                    branch_record = self.env['github.branch'].create({
                        'name': branch['name'],
                        'project_id': project.id,
                        'commit_sha': branch['commit']['sha']
                    })

                    # Crear tarea vinculada al proyecto para cada rama
                    task = self.env['project.task'].create({
                        'branch_id': branch_record.id,
                        'name': branch['name'],
                        'project_id': project.id,
                        'stage_id': project_type.id,
                        'description': f"Rama asociada: {branch['name']}\nSHA: {branch['commit']['sha']}",
                    })
            else:
                raise UserError(_(f"Error al conectar con GitHub: {response.json().get('message')}"))

        except Exception as e:
            raise UserError(_(f"Ocurrió un error: {str(e)}"))
