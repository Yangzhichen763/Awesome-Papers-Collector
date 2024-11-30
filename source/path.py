import os


def get_root_path():
    path = os.path.abspath(__file__)

    path = os.path.dirname(path)
    path = os.path.dirname(path)
    return path


root = get_root_path()


if __name__ == '__main__':
    print(get_root_path())