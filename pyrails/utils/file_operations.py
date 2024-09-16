def insert_line_without_duplicating(file_path, line):
    with open(file_path, "r") as f:
        lines = f.readlines()
        if line.strip() not in [l.strip() for l in lines]:
            lines.append(line)

    with open(file_path, "w") as f:
        f.write("".join(lines))
