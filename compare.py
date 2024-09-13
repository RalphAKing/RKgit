from flask import Flask, render_template, request, redirect, url_for
import os
import difflib

app = Flask(__name__)

# Define the base directory where projects are stored
BASE_DIR = 'projects/'

def get_project_versions(project_name):
    """Returns a list of version directories for a given project."""
    project_path = os.path.join(BASE_DIR, project_name)
    if os.path.exists(project_path):
        return sorted([d for d in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, d))])
    return []

def compare_file_lists(old_version_files, new_version_files):
    """Compares files in two versions and returns a list of files and their status (added, removed, unchanged)."""
    old_set = set(old_version_files)
    new_set = set(new_version_files)

    # Files removed in the new version
    removed_files = old_set - new_set
    # Files added in the new version
    added_files = new_set - old_set
    # Files present in both versions
    unchanged_files = old_set & new_set

    file_status = []
    for file in sorted(unchanged_files):
        file_status.append((file, 'unchanged'))
    for file in sorted(removed_files):
        file_status.append((file, 'removed'))
    for file in sorted(added_files):
        file_status.append((file, 'added'))

    return file_status

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        project_name = request.form['project']
        return redirect(url_for('select_versions', project_name=project_name))

    projects = sorted([d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))])
    return render_template('index.html', projects=projects)

@app.route('/versions/<project_name>', methods=['GET', 'POST'])
def select_versions(project_name):
    if request.method == 'POST':
        version1 = request.form['version1']
        version2 = request.form['version2']
        return redirect(url_for('explore_project', project_name=project_name, version1=version1, version2=version2))

    versions = get_project_versions(project_name)
    return render_template('versions.html', project_name=project_name, versions=versions)

@app.route('/explore/<project_name>/<version1>/<version2>')
def explore_project(project_name, version1, version2):
    old_version_path = os.path.join(BASE_DIR, project_name, version1)
    new_version_path = os.path.join(BASE_DIR, project_name, version2)

    old_version_files = [os.path.relpath(os.path.join(dp, f), old_version_path) 
                         for dp, dn, filenames in os.walk(old_version_path) for f in filenames]
    new_version_files = [os.path.relpath(os.path.join(dp, f), new_version_path) 
                         for dp, dn, filenames in os.walk(new_version_path) for f in filenames]

    files_status = compare_file_lists(old_version_files, new_version_files)

    return render_template('explorer.html', project_name=project_name, version1=version1, version2=version2, files_status=files_status)

@app.route('/compare/<project_name>/<version1>/<version2>/<path:filename>')
def compare_files(project_name, version1, version2, filename):
    old_file_path = os.path.join(BASE_DIR, project_name, version1, filename)
    new_file_path = os.path.join(BASE_DIR, project_name, version2, filename)

    old_file_exists = os.path.exists(old_file_path)
    new_file_exists = os.path.exists(new_file_path)

    if old_file_exists and new_file_exists:
        with open(old_file_path, 'r') as f1:
            old_file_content = f1.readlines()
        with open(new_file_path, 'r') as f2:
            new_file_content = f2.readlines()
        diff_html = generate_file_diff(old_file_content, new_file_content)
        return render_template('compare.html', filename=filename, diff_html=diff_html)

    elif old_file_exists:
        with open(old_file_path, 'r') as f1:
            old_file_content = f1.readlines()
        return render_template('single_file.html', filename=filename, content=old_file_content, version='Old')

    elif new_file_exists:
        with open(new_file_path, 'r') as f2:
            new_file_content = f2.readlines()
        return render_template('single_file.html', filename=filename, content=new_file_content, version='New')

    else:
        return "File not found in either version."

def generate_file_diff(file1_lines, file2_lines):
    """Generates a diff view for two sets of lines."""
    diff = list(difflib.ndiff(file1_lines, file2_lines))

    result_html = []
    old_line_num = 1  # Line number for the old file
    new_line_num = 1  # Line number for the new file

    for line in diff:
        if line.startswith('-'):
            result_html.append((
                old_line_num, 'X', 'removed', line[2:].replace('<', '&lt;').replace('>', '&gt;')
            ))
            old_line_num += 1
        elif line.startswith('+'):
            result_html.append((
                'X', new_line_num, 'added', line[2:].replace('<', '&lt;').replace('>', '&gt;')
            ))
            new_line_num += 1
        elif not line.startswith('?'):
            result_html.append((
                old_line_num, new_line_num, 'unchanged', line[2:].replace('<', '&lt;').replace('>', '&gt;')
            ))
            old_line_num += 1
            new_line_num += 1

    return result_html

if __name__ == '__main__':
    app.run(debug=True)
