welcome_message = (
    "Hi {name}, I'm Zhambyl tipo imitator bot 🤖 \nPlease setup your account before all"
)
creds_format = "Send account info in format: \n{format}"
command_buttons = [
    {"name": "Set account", "callback_data": "set_account"},
    {"name": "Get account info", "callback_data": "get_account"},
    {"name": "Get schedule", "callback_data": "get_schedule"},
    {"name": "Visit all lessons", "callback_data": "visit_lesson"},
    {"name": "Get home works", "callback_data": "get_home_work"},
    {"name": "Get class works", "callback_data": "get_class_work"},
]
account_info = (
    "Name: {name} \nTelegram id: {telegram_id} \nTipo account email: {tipo_email}"
)
schedule_text = (
    "Time: {time} \n"
    "Teacher name: {name} \n"
    "Subject: {subject} \n"
    "Lecture count: {lecture} \n"
    "Format: {format} \n"
    "Link for subject: {link} \n\n"
)
visit_lessons = "Visited lesson: {lesson_name} \nLink: {link}\n\n"
hw_desc = (
    "Name: {name} \n\n"
    "Description: {desc} \n\n"
    "Teacher: {teacher} \n\n"
    "Deadline: {deadline} \n\n"
    "Created at: {date} \n\n"
)
cw_desc = (
    "Subject: {subject} \n\n"
    "Desc: \n{desc} \n\n"
    "Group: {group} \n"
    "Teacher: {teacher} \n\n"
    "Date: {date} \n"
    "Created at: {created_at} \n"
    "Updated at: {updated_at}"
)
no_type_works = "No {type_} works"
