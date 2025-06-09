import toml

def load_project(path):
    return toml.load(path)
