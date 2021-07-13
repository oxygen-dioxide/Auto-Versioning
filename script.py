from os import getenv
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from json import loads

token = loads(getenv('TOKEN', '""'))
before = getenv('BEFORE', '')
after = getenv('AFTER', '')
repo = getenv('REPO', '')

def parse_changes(files: list) -> bool:
    changelog = {"added": [], "renamed": [], "deleted": [], "changed": []}
    major = False
    for file in files:
        status = file['status']
        if not major:
            if status == 'renamed' or status == 'added':
                major = True
        filename = file['filename']
        if status == 'renamed':
            changelog['renamed'].append('`'+file['previous_filename']+'` → `'+filename+'`')
        if status == 'added':
            changelog['added'].append('`'+filename+'`')
        if status == 'removed':
            changelog['deleted'].append('`'+filename+'`')
        if status == 'changed':
            changelog['deleted'].append('`'+filename+'`')
    return changelog, major

def get_data(url: str) -> str:
    request = Request(url, headers={'Authorization': 'token '+token})
    result = urlopen(request, data=bytes('{"accept": "application/vnd.github.v3+json"}', encoding='utf8'))
    return loads(result)

def gen_new_tag(major: bool, tag: str) -> str:
    tag = ''.join([i for i in tag if i.isnumeric() or i == '.']).split('.')
    tag = [int(i) for i in tag]
    if major:
        try:
            tag[1] += 1
        except IndexError:
            tag.append(0)
    else:
        try:
            tag[2] += 1
        except IndexError:
            tag.append(0)
            if len(tag) < 2:
                tag.append(0)
    return '.'.join(tag)

if __name__ == '__main__':
    files = get_data(f'https://api.github.com/repos/{repo}/compare/{before}...{after}')['files']
    changelog, major = parse_changes(files)
    tag = get_data(f'https://api.github.com/repos/{repo}/tags')[0]['name']
    if not tag:
        tag = getenv('FALLBACK_TAG', '0.0')
    else:
        tag = gen_new_tag(major, tag)
    changelog_str = ''
    for change, values in changelog.items():
        if values:
            changelog_str += change.title()+': '+'\n- '.join(values)+'\n'
    print('::set-output name=tag::'+tag)
    print('::set-output name=changelog::'+changelog_str)