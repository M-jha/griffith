import os
import requests
from flask import jsonify, request


class GitHubResource:
    """
    Class to manage GitHub organization members, repositories, and user access.
    """

    def __init__(self, org_name):
        """
        Initialize the GitHubResource class with a personal access token (PAT) from environment variable and organization name.

        Parameters:
            org_name (str): Name of the GitHub organization to manage.
        """
        self.github_pat = os.getenv("GIT_SECRET")  # Retrieve GitHub PAT from environment variable
        if not self.github_pat:
            raise ValueError("GitHub Personal Access Token not found in environment variables.")
        self.org_name = org_name
        self.base_url = "https://api.github.com"

    def get_org_members(self):
        """
        Fetch the list of members in the GitHub organization.

        Returns:
            tuple: A tuple containing a JSON response with the list of members or an error message.
        """
        url = f"{self.base_url}/orgs/{self.org_name}/members"
        headers = {"Authorization": f"token {self.github_pat}"}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            members = response.json()
            member_list = [{"username": member['login']} for member in members]
            return jsonify({"data": member_list}), 200
        else:
            return jsonify({
                               "error": f"Failed to retrieve members: {response.status_code} - {response.text}"}), response.status_code

    def get_org_repos(self):
        """
        Fetch the list of repositories in the GitHub organization.

        Returns:
            tuple: A tuple containing a JSON response with the list of repositories or an error message.
        """
        url = f"{self.base_url}/orgs/{self.org_name}/repos"
        headers = {"Authorization": f"token {self.github_pat}"}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            repos = response.json()
            repo_list = [{"name": repo['name'], "url": repo['html_url']} for repo in repos]
            return jsonify({"repositories": repo_list}), 200
        else:
            return jsonify({
                               "error": f"Failed to retrieve repositories: {response.status_code} - {response.text}"}), response.status_code

    def get_user_access_level(self):
        """
        Get the access level of a user for a specific repository in the organization.

        Returns:
            tuple: A tuple containing a JSON response with the access level or an error message.
        """
        username = request.args.get('username')
        repo = request.args.get('repo')
        headers = {"Authorization": f"token {self.github_pat}"}

        if not username or not repo:
            return jsonify({"error": "Missing username or repo parameter"}), 400

        url = f"{self.base_url}/repos/{self.org_name}/{repo}/collaborators/{username}/permission"

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            access_data = response.json()
            access_level = access_data.get('permission', 'none')
            return jsonify({"accessLevel": access_level}), 200
        else:
            return jsonify({
                               "error": f"Failed to retrieve access level: {response.status_code} - {response.text}"}), response.status_code

    def manage_user_access(self):
        """
        Manage (add or update) a user's access level for a specific repository in the organization.

        Returns:
            tuple: A tuple containing a JSON response with success or error message.
        """
        data = request.get_json()
        username = data.get('username')
        repo = data.get('repo')
        access = data.get('access')

        if not username or not repo or not access:
            return jsonify({"error": "Missing username, repo, or access level"}), 400

        headers = {
            'Authorization': f'Bearer {self.github_pat}',
            'Accept': 'application/vnd.github.v3+json'
        }
        url = f"{self.base_url}/repos/{self.org_name}/{repo}/collaborators/{username}"
        payload = {"permission": access}

        try:
            response = requests.put(url, headers=headers, json=payload)

            success_message = {"message": f"Access level for {username} has been updated to {access} in {repo}."}

            if response.status_code in [201, 204]:
                return jsonify(success_message), 200
            else:
                return jsonify({
                                   "error": f"Failed to manage access: {response.status_code} - {response.text}"}), response.status_code
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500

    def create_repo(self, repo_name, private=True):
        """
        Create a new repository in the GitHub organization.

        Parameters:
            repo_name (str): Name of the repository to create.
            private (bool): Whether the repository should be private or public (default is True).

        Returns:
            tuple: A tuple containing a JSON response with repository details or an error message.
        """
        url = f"{self.base_url}/orgs/{self.org_name}/repos"
        headers = {
            'Authorization': f'Bearer {self.github_pat}',
            'Accept': 'application/vnd.github.v3+json'
        }
        payload = {
            "name": repo_name,
            "private": private,
            "auto_init": True,
            "gitignore_template": "Python"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 201:
                return jsonify({"message": f"Repository '{repo_name}' created successfully"}), 201
            else:
                return jsonify({
                                   "error": f"Failed to create repository: {response.status_code} - {response.text}"}), response.status_code
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500

    def delete_repo(self, repo_name):
        """
        Delete a repository from the GitHub organization.

        Parameters:
            repo_name (str): Name of the repository to delete.

        Returns:
            tuple: A tuple containing a JSON response with success or error message.
        """
        url = f"{self.base_url}/repos/{self.org_name}/{repo_name}"
        headers = {"Authorization": f"token {self.github_pat}"}

        response = requests.delete(url, headers=headers)

        if response.status_code == 204:
            return jsonify({"message": f"Repository '{repo_name}' deleted successfully"}), 204
        else:
            return jsonify({
                               "error": f"Failed to delete repository: {response.status_code} - {response.text}"}), response.status_code
