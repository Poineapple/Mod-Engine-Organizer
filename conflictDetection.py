import os


def conflictDetector(root_dir):
    file_paths = {}  # Key: file name, Value: list of paths
    conflicts = {}

    # Walk through the directory
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            rel_dir = os.path.relpath(root, root_dir)
            rel_file_path = os.path.join(rel_dir, file)
            if file in file_paths:
                file_paths[file].append(rel_file_path)
            else:
                file_paths[file] = [rel_file_path]

    # Identify duplicates
    duplicates = {file: paths for file,
                  paths in file_paths.items() if len(paths) > 1}

    # Store duplicates in the conflicts dictionary
    for paths in duplicates.values():
        for path in paths:
            level_1_folder = path.split(os.sep)[0]
            if level_1_folder in conflicts:
                conflicts[level_1_folder].append(path)
            else:
                conflicts[level_1_folder] = [path]

    return conflicts


# Example usage
mod_root = 'D:/Games/elden rang mods/ModEngine-2.1.0.0-win64/mod'
dict = conflictDetector(mod_root)

for i in dict:
	print(i)
	for j in dict[i]:
		print(j)
	print("\n")
