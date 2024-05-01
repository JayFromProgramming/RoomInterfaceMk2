

def parse_net_err_message(message):
    message = message.split("server replied: ")[1]
    return message

