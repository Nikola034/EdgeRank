import datetime


def load_friends(path):
    output_data = {}
    with open(path, encoding='utf-8') as file:
        lines = file.readlines()

        for line_index in range(1, len(lines)):
            line = lines[line_index]
            values = line.split(',')

            values[-1] = values[-1].strip()
            person = values[0]
            friends = values[2:]
            output_data[person] = friends

    return output_data


def load_comments(path):
    output_data = {}
    with open(path, encoding="utf-8") as file:
        lines = file.readlines()
        comment = ""
        found_open_ellipsis = False
        found_close_ellipsis = False

        for index in range(1, len(lines)):
            line = lines[index]

            if line == "\n":
                comment += line

            if line[-1] == "\n":
                line = line[:-1]

            first_index = line.index("\"") if "\"" in line else -1
            if first_index > -1:
                found_open_ellipsis = True

            next_index = line.index("\"", first_index + 1) if "\"" in line[first_index + 1:] else -1
            if next_index > -1:
                found_close_ellipsis = True

            if found_open_ellipsis and not found_close_ellipsis:
                comment += line
                continue
            else:
                comment = line

            data = comment.split(",")
            n = len(data)

            if n < 14:
                raise Exception("Comment does not contain necessary data.")
            elif n > 14:
                comment_text = "".join(data[3:n - 10])
            else:
                comment_text = data[3]

            content = {
                "comment_id": data[0],
                "status_id": data[1],
                "parent_id": data[2],
                "comment_message": comment_text,
                "comment_author": data[n - 10],
                "comment_published": datetime.datetime.strptime(data[n - 9], "%Y-%m-%d %H:%M:%S"),
                "num_reactions": int(data[n - 8]),
                "num_likes": int(data[n - 7]),
                "num_loves": int(data[n - 6]),
                "num_wows": int(data[n - 5]),
                "num_hahas": int(data[n - 4]),
                "num_sads": int(data[n - 3]),
                "num_angrys": int(data[n - 2]),
                "num_special": int(data[n - 1])
            }

            if data[n - 10] not in output_data:
                output_data[data[n - 10]] = []
            output_data[data[n - 10]].append(content)

            found_open_ellipsis = found_close_ellipsis = False
            comment = ""

    return output_data


def load_statuses(path):
    extracted_statuses = {}
    with open(path, encoding="utf-8") as file:
        lines = file.readlines()
        comment = ""
        paired_ellipses = True

        for index in range(1, len(lines)):
            line = lines[index]

            if line == "\n":
                comment += line
                continue

            # if line[-1] == "\n":
            #     line = line[:-1]
            line = line.strip()

            previous_index = -1

            while True:
                index = line.index("\"", previous_index + 1) if "\"" in line[previous_index + 1:] else -1
                if index == -1:
                    break
                paired_ellipses = not paired_ellipses
                previous_index = index

            comment += line
            if not paired_ellipses:
                continue

            data = comment.split(",")
            n = len(data)

            if n < 16:
                raise Exception("Status does not contain necessary data.")
            elif n > 16:
                comment_text = "".join(data[1:n - 14])
            else:
                comment_text = data[1]

            content = {
                "status_id": data[0],
                "status_message": comment_text,
                "status_type": data[n - 14],
                "status_link": data[n - 13],
                "status_published": datetime.datetime.strptime(data[n - 12], "%Y-%m-%d %H:%M:%S"),
                "author": data[n - 11],
                "num_reactions": int(data[n - 10]),
                "num_comments": int(data[n - 9]),
                "num_shares": int(data[n - 8]),
                "num_likes": int(data[n - 7]),
                "num_loves": int(data[n - 6]),
                "num_wows": int(data[n - 5]),
                "num_hahas": int(data[n - 4]),
                "num_sads": int(data[n - 3]),
                "num_angrys": int(data[n - 2]),
                "num_special": int(data[n - 1])
            }

            extracted_statuses[data[0]] = content

            comment = ""
            paired_ellipses = True

    return extracted_statuses


def load_shares(path):
    shares = {}
    with open(path, encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines[1:]:
            line_strip = line.strip().split(",")

            content = {
                "status_id": line_strip[0],
                "sharer": line_strip[1],
                "status_shared": datetime.datetime.strptime(line_strip[2], "%Y-%m-%d %H:%M:%S")
            }

            if line_strip[1] not in shares:
                shares[line_strip[1]] = []
            shares[line_strip[1]].append(content)

    return shares


def load_reactions(path):
    reactions = {}
    with open(path, encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines[1:]:
            line_strip = line.strip().split(",")

            content = {
                "status_id": line_strip[0],
                "type_of_reaction": line_strip[1],
                "reactor": line_strip[2],
                "reacted": datetime.datetime.strptime(line_strip[3], "%Y-%m-%d %H:%M:%S")
            }

            if line_strip[2] not in reactions:
                reactions[line_strip[2]] = []
            reactions[line_strip[2]].append(content)

    return reactions