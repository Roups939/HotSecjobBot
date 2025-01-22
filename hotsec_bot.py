import logging
import csv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from collections import Counter

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
CHOOSING_VACANCY, CHOOSING_REGION = range(2)
regions = {
    'москва': 1,
    'санкт-петербург': 2,
    'екатеринбург': 3,
    'новосибирск': 4,
    'нижний новгород': 7,
    'казань': 9,
    'челябинск': 10,
    'самара': 11,
    'омск': 13,
    'ростов-на-дону': 14,
    'уфа': 99,
    'красноярск': 120
}
VACANCIES = [
    'кибербезопасность',
    'DevSecOps',
    'пентестер',
    'антифрод-аналитик',
    'руководитель отдела информационной безопасности',
    'аналитик по расследованию компьютерных инцидентов',
    'архитектор информационной безопасности'
]
def read_vacancies_from_csv(region_id):
    filename = f'{region_id}_vacancies.csv'
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return list(reader)
    except FileNotFoundError:
        return None
def calculate_average_salary(vacancies):
    salaries = []
    for vacancy in vacancies:
        salary = vacancy['Зарплата']
        if salary and salary != 'Не указана':
            parts = salary.split()
            if len(parts) >= 3:
                try:
                    from_value = float(parts[0]) if parts[0] != 'None' else None
                    to_value = float(parts[2]) if parts[2] != 'None' else None
                    if from_value is not None and to_value is not None:
                        avg_salary = (from_value + to_value) / 2
                        salaries.append(avg_salary)
                except ValueError:
                    continue
    return sum(salaries) / len(salaries) if salaries else None
def analyze_requirements(vacancies):
    requirements = []
    for vacancy in vacancies:
        description = vacancy['Требования']
        if description:
            requirements.append(description.lower())

    skills = [
        'python', 'java', 'c++', 'c#', 'javascript', 'go', 'typescript', 
        'security', 'cloud', 'networking', 'aws', 'azure', 'linux', 'docker', 
        'kubernetes', 'git', 'ci/cd', 'sql', 'mongodb', 'postgresql', 
        'api', 'rest', 'graphql', 'devops', 'microservices'
    ]
    skill_counts = Counter()

    for req in requirements:
        for skill in skills:
            if skill in req:
                skill_counts[skill] += 1

    return skill_counts.most_common(5)
def generate_recommendations(common_skills, profession):
    if not common_skills:
        return "Нет данных для рекомендаций."
    profession_recommendations = {
        'кибербезопасность': {
            'базовые': ['python', 'linux', 'networking'],
            'продвинутые': ['aws', 'docker', 'kubernetes'],
            'сертификации': ['CISSP', 'CEH']
        },
        'DevSecOps': {
            'базовые': ['git', 'ci/cd', 'docker'],
            'продвинутые': ['kubernetes', 'aws', 'azure'],
            'сертификации': ['AWS Certified Security', 'Certified Kubernetes Administrator']
        },
        'пентестер': {
            'базовые': ['ethical hacking', 'python', 'networking'],
            'продвинутые': ['penetration testing', 'owasp', 'reverse engineering'],
            'сертификации': ['OSCP', 'CEH']
        },
        'антифрод-аналитик': {
            'базовые': ['data analysis', 'sql', 'python'],
            'продвинутые': ['machine learning', 'big data', 'fraud detection'],
            'сертификации': ['CFE', 'CAMS']
        },
        'руководитель отдела информационной безопасности': {
            'базовые': ['project management', 'risk management', 'compliance'],
            'продвинутые': ['leadership', 'strategic planning', 'budgeting'],
            'сертификации': ['CISSP', 'CISM']
        },
        'аналитик по расследованию компьютерных инцидентов': {
            'базовые': ['forensics', 'incident response', 'networking'],
            'продвинутые': ['malware analysis', 'threat intelligence', 'SIEM'],
            'сертификации': ['GCFA', 'GCIH']
        },
        'архитектор информационной безопасности': {
            'базовые': ['security architecture', 'networking', 'cloud security'],
            'продвинутые': ['zero trust architecture', 'devsecops', 'threat modeling'],
            'сертификации': ['CISSP-ISSAP', 'TOGAF']
        }
    }
    recommendations = profession_recommendations.get(profession.lower(), {})
    top_skills = [skill for skill, _ in common_skills[:3]]
    result = []
    if top_skills:
        result.append(f"Самые востребованные навыки: {', '.join(top_skills)}.")
    
    if recommendations.get('базовые'):
        result.append(f"Базовые навыки: {', '.join(recommendations['базовые'])}.")
    
    if recommendations.get('продвинутые'):
        result.append(f"Продвинутые навыки: {', '.join(recommendations['продвинутые'])}.")
    
    if recommendations.get('сертификации'):
        result.append(f"Рекомендуемые сертификации: {', '.join(recommendations['сертификации'])}.")
    
    return "\n".join(result) if result else "Нет данных для рекомендаций."
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Привет! Выбери вакансию из списка:\n"
        "1. Кибербезопасность\n"
        "2. DevSecOps\n"
        "3. Пентестер\n"
        "4. Антифрод-аналитик\n"
        "5. Руководитель отдела информационной безопасности\n"
        "6. Аналитик по расследованию компьютерных инцидентов\n"
        "7. Архитектор информационной безопасности\n\n"
        "Введи номер вакансии (1-7)."
    )
    return CHOOSING_VACANCY
async def choose_vacancy(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text.strip()
    if not user_input.isdigit() or int(user_input) < 1 or int(user_input) > 7:
        await update.message.reply_text("Пожалуйста, введи номер вакансии от 1 до 7.")
        return CHOOSING_VACANCY

    vacancy_index = int(user_input) - 1
    context.user_data['vacancy'] = VACANCIES[vacancy_index]

    await update.message.reply_text(
        "Теперь введи регион из доступных:\n"
        "Москва, Санкт-Петербург, Екатеринбург, Новосибирск, Нижний Новгород, Казань, Челябинск, Самара, Омск, Ростов-на-Дону, Уфа, Красноярск."
    )
    return CHOOSING_REGION
async def choose_region(update: Update, context: CallbackContext) -> int:
    region = update.message.text.strip().lower()
    if region not in regions:
        await update.message.reply_text("Указанный регион не поддерживается. Пожалуйста, выбери регион из списка.")
        return CHOOSING_REGION
    context.user_data['region'] = region
    region_id = regions[region]
    vacancies = read_vacancies_from_csv(region_id)
    if not vacancies:
        await update.message.reply_text(f"Для региона {region.title()} нет данных о вакансиях.")
        return ConversationHandler.END
    selected_vacancy = context.user_data['vacancy']
    filtered_vacancies = [v for v in vacancies if selected_vacancy.lower() in v['Профессия'].lower()]
    if not filtered_vacancies:
        await update.message.reply_text(f"В регионе {region.title()} нет вакансий по специальности '{selected_vacancy.title()}'.")
        return ConversationHandler.END
    avg_salary = calculate_average_salary(filtered_vacancies)
    avg_salary_text = f"Средняя зарплата: {avg_salary:.2f} руб." if avg_salary else "Зарплата не указана."

    common_skills = analyze_requirements(filtered_vacancies)
    recommendations = generate_recommendations(common_skills, selected_vacancy)
    await update.message.reply_text(
        f"Специальность: {selected_vacancy.title()}\n"
        f"Регион: {region.title()}\n"
        f"Найдено вакансий: {len(filtered_vacancies)}\n\n"
        f"{avg_salary_text}\n"
        f"Рекомендации:\n{recommendations}"
    )
    return ConversationHandler.END
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Диалог завершен.")
    return ConversationHandler.END
def main():
    application = Application.builder().token("token!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!").build()## Вставь токен,я его потерял!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_VACANCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_vacancy)],
            CHOOSING_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_region)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()