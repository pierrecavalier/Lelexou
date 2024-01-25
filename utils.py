from datetime import datetime, timedelta
import os


def wait_until_3am():
    now = datetime.now()
    three_time = now.replace(hour=3, minute=0, second=0, microsecond=0)
    if now.time() >= three_time.time():
        three_time += timedelta(days=1)
    return (three_time - now).total_seconds()


def format_remaining_time(seconds):
    time_delta = timedelta(seconds=seconds)
    months = time_delta.days // 30
    days = time_delta.days % 30
    hours = time_delta.seconds // 3600
    minutes = (time_delta.seconds % 3600) // 60
    seconds = time_delta.seconds % 60

    time_format = ""
    if months > 0:
        time_format += f"{months} mois, "
    if days > 0:
        time_format += f"{days} jour{'s' if days > 1 else ''}, "
    if hours > 0:
        time_format += f"{hours} heure{'s' if hours > 1 else ''}, "
    if minutes > 0:
        time_format += f"{minutes} minute{'s' if minutes > 1 else ''}, "
    time_format += f"{seconds} seconde{'s' if seconds > 1 else ''}"

    return time_format

def split_message_at_sentence_or_paragraph(message, max_length=2000):
    if len(message) <= max_length:
        return [message]
    
    parts = []
    while len(message) > 0:
        # If the remaining message is short enough, add it as the final part
        if len(message) <= max_length:
            parts.append(message)
            break
        
        # Find the last full stop or paragraph break within the max_length
        cut_index_period = message.rfind('.', 0, max_length)
        cut_index_paragraph = message.rfind('\n\n', 0, max_length)
        
        # Choose the larger of the two indices to ensure we're cutting at the end of a paragraph if possible
        cut_index = max(cut_index_period, cut_index_paragraph)
        
        if cut_index == -1:  # if neither found, we'll cut it at max_length
            cut_index = max_length
        
        parts.append(message[:cut_index + 1])  # +1 to include the full stop or the paragraph break
        message = message[cut_index + 1:].strip()  # Remove leading spaces in the next part

    return parts


def log(message):
    if message == "":
        formatted_message = "\n"
    else:
        formatted_message = f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - {message} \n"
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, "log.txt")
    with open(log_file, "a") as file:
        file.write(formatted_message)
    print(formatted_message)
