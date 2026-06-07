"""
TARRIFIC HOST BOT - Vercel Deployment
Deploy GitHub repos to Vercel via REST API
"""
import requests
import json
from config import VERCEL_TOKEN

VERCEL_API_BASE = "https://api.vercel.com"

class VercelDeployer:
    def __init__(self, token=None):
        self.token = token or VERCEL_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def deploy_from_github(self, repo_url, project_name=None):
        """
        Deploy a GitHub repository to Vercel

        repo_url: GitHub repo URL (e.g., https://github.com/user/repo)
        project_name: Optional custom name for Vercel project
        """
        if not self.token:
            return {
                'success': False,
                'error': 'No Vercel token configured. Add VERCEL_TOKEN to config.py'
            }

        try:
            # Extract owner/repo from GitHub URL
            parts = repo_url.replace('https://github.com/', '').replace('http://github.com/', '').split('/')
            if len(parts) < 2:
                return {
                    'success': False,
                    'error': 'Invalid GitHub repo URL. Format: https://github.com/user/repo'
                }

            owner = parts[0]
            repo = parts[1].replace('.git', '')

            # Create project and deploy
            project_name = project_name or f"{repo}-tarrific"

            # Step 1: Create project
            create_project_url = f"{VERCEL_API_BASE}/v9/projects"
            project_data = {
                "name": project_name,
                "gitRepository": {
                    "repo": f"{owner}/{repo}",
                    "type": "github"
                }
            }

            response = requests.post(
                create_project_url,
                headers=self.headers,
                json=project_data,
                timeout=30
            )

            if response.status_code not in [200, 201]:
                return {
                    'success': False,
                    'error': f'Failed to create Vercel project: {response.text}',
                    'status': response.status_code
                }

            project_info = response.json()
            project_id = project_info.get('id')

            # Step 2: Trigger deployment
            deploy_url = f"{VERCEL_API_BASE}/v13/deployments"
            deploy_data = {
                "name": project_name,
                "project": project_id,
                "gitSource": {
                    "type": "github",
                    "repoId": project_info.get('gitRepository', {}).get('repoId'),
                    "ref": "main",
                    "repo": f"{owner}/{repo}",
                    "org": owner
                },
                "target": "production"
            }

            deploy_response = requests.post(
                deploy_url,
                headers=self.headers,
                json=deploy_data,
                timeout=30
            )

            if deploy_response.status_code not in [200, 201]:
                return {
                    'success': False,
                    'error': f'Failed to trigger deployment: {deploy_response.text}',
                    'status': deploy_response.status_code
                }

            deploy_info = deploy_response.json()

            return {
                'success': True,
                'project_id': project_id,
                'project_name': project_name,
                'deployment_id': deploy_info.get('id'),
                'url': deploy_info.get('url'),
                'inspector_url': deploy_info.get('inspectorUrl'),
                'state': deploy_info.get('state', 'pending')
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    def get_deployment_status(self, deployment_id):
        """Check deployment status"""
        try:
            url = f"{VERCEL_API_BASE}/v13/deployments/{deployment_id}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'state': data.get('state'),
                    'url': data.get('url'),
                    'readyState': data.get('readyState')
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to check status: {response.status_code}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def list_projects(self):
        """List all Vercel projects"""
        try:
            url = f"{VERCEL_API_BASE}/v9/projects"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                projects = data.get('projects', [])
                return {
                    'success': True,
                    'projects': [
                        {
                            'name': p.get('name'),
                            'id': p.get('id'),
                            'url': f"https://{p.get('name')}.vercel.app"
                        }
                        for p in projects
                    ]
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to list projects: {response.status_code}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
