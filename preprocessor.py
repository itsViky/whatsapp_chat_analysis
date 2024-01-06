import re
import pandas as pd
from datetime import datetime

def preprocess(data):
    # droping the links and media omitted lines
    data = re.sub(r'https?://\S+|<Media omitted>', '', data)
    pattern = re.compile(r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}\s[APMapm]{2}\s-\s[^:\n]*:[^\n]*$)')

    # Filter out lines containing URLs or '<Media omitted>'
    filtered_lines = [line.strip() for line in data.split('\n') if not re.search(r'http[s]?://', line) and '<Media omitted>' not in line]

    #Extract lines matching the desired format
    data = [match.group(1) for line in filtered_lines if (match := pattern.search(line))]

    dates1 = []
    messages = []

    for line in data:
        #Use regular expression to extract date and message
        match = re.match(r'(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{1,2}\s*[APMapm]+) - (.+)', line)

        if match:
           date = match.group(1)
           message = match.group(2)

        dates1.append(date)
        messages.append(message)
        
    # Function to convert 12-hour format to 24-hour format
    def convert_to_24_hour_format(date_str):
        date_object = datetime.strptime(date_str, '%m/%d/%y, %I:%M\u202f%p')
        return date_object.strftime('%m/%d/%y, %H:%M')

    # Convert and store in 'dates' list
    dates = [convert_to_24_hour_format(date) for date in dates1]

    # Concatenate " - " at the end of each item
    dates = [item + " - " for item in dates]

    # Function to convert mm/dd/yyyy to dd/mm/yyyy
    def convert_date_format(date_str):
        date_object = datetime.strptime(date_str, '%m/%d/%y, %H:%M - ')
        return date_object.strftime('%d/%m/%y, %H:%M - ')

    # Convert the date format for each item in the list
    dates = [convert_date_format(item) for item in dates]

    df = pd.DataFrame({'user_message': messages, 'message_date': dates})
    df['message_date'] = pd.to_datetime(df['message_date'], format='%d/%m/%y, %H:%M - ')
    df.rename(columns={'message_date': 'date'}, inplace=True)

    users = []
    messages = []
    for message in df['user_message']:
        entry = re.split('([\w\W]+?):\s', message)
        if entry[1:]:  # user name
            users.append(entry[1])
            messages.append(" ".join(entry[2:]))
        else:
            users.append('Group_Notification')
            messages.append(entry[0])

    df['user'] = users
    df['message'] = messages
    df.drop(columns=['user_message'], inplace=True)

    #spliting the date, time, month, year details
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    # droping the group notifications
    df = df[~df.isin(['Group_Notification']).any(axis=1)]

    return df