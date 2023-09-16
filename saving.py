import json


def read_db(db_file_name):
    try:
        with open(db_file_name, "r") as read_file:
            data = json.load(read_file)
            return data
    except:
        with open(db_file_name, "w") as read_file:
            data = {}
            json.dump(data, read_file)
            return {}

def write_number_to_db(db_file_name, email_account, mail_number):
    data = read_db(db_file_name)

    with open(db_file_name, "w") as read_file:
        data[email_account] = mail_number
        # print(data)
        json.dump(data, read_file)
        return True